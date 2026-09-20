import json
from pathlib import Path
import numpy as np
import pytest
from fastapi.testclient import TestClient
from gateway.app import app
from gateway.validation import validate
from controller.pipeline import run_pipeline
from verification.engine import normalized_difference,verify
from training.make_demo import write_tif
ROOT=Path(__file__).resolve().parents[1]
DEMOS=json.loads((ROOT/'data/demo/manifest.json').read_text())

@pytest.mark.parametrize('demo',DEMOS,ids=lambda d:d['id'])
def test_all_scenarios(demo):
    emitted=[]
    out=run_pipeline([ROOT/p for p in demo['paths']],demo['options'],demo['scenario'],demo['query'],emit=emitted.append)
    assert 0<=out['trust_score']<=1
    assert emitted==out['execution_trace']
    assert {'classify_intent','select_model','execute','symbolic_verification','consensus','report'}<={e['action'] for e in emitted}
    assert [e['step'] for e in emitted]==list(range(1,len(emitted)+1))
    if demo['id'] in ('grounding','change'):assert out['overlay']['data']
    if demo['id']=='fusion':assert any('Optical/SAR disagreement' in f for f in out['flags'])

def test_indices_are_real_math():
    x=normalized_difference(np.array([.8,0,np.nan]),np.array([.2,0,1]))
    assert x[0]==pytest.approx(.6)
    assert np.isnan(x[1:]).all()

def test_missing_bands_cannot_agree():
    d=DEMOS[0];bundle=validate([ROOT/d['paths'][0]],d['options'],'SINGLE')
    bundle['images'][0]['array']=bundle['images'][0]['array'][:3];bundle['images'][0]['bands']=['red','green','blue']
    out=verify(bundle,[{'neural_confidence':.8,'claims':[{'type':'water','fraction':.8}]}])
    assert out['symbolic_agreement'] is None
    assert out['verification_coverage']==0
    assert out['trust_score']==pytest.approx(.32)

def test_contradiction_is_exposed():
    d=DEMOS[0];bundle=validate([ROOT/d['paths'][0]],d['options'],'SINGLE')
    out=verify(bundle,[{'neural_confidence':.8,'claims':[{'type':'water','fraction':.99}]}])
    assert out['checks'][0]['status']=='disagrees'
    assert any('disagrees' in f for f in out['flags'])

def test_rgb_accepts_ordinary_uploads():
    assert validate([ROOT/'data/demo/optical_before.png'],[{}],'SINGLE')['images'][0]['visual_only']

def test_temporal_order_rejected():
    d=DEMOS[2]
    with pytest.raises(ValueError,match='earlier'):validate([ROOT/p for p in d['paths']],list(reversed(d['options'])),d['scenario'])

def test_grid_mismatch(tmp_path):
    import rasterio
    from rasterio.transform import from_origin
    path=tmp_path/'different.tif';write_tif(path,np.ones((5,256,256),dtype='float32'),['red','green','blue','nir','swir'])
    with rasterio.open(path,'r+') as ds:ds.transform=from_origin(650001,1450000,10,10)
    out=validate([ROOT/'data/demo/optical_before.tif',path],DEMOS[2]['options'],'BITEMPORAL_PAIR')
    assert out['images'][1]['was_resampled']

def test_registry_rejects_unknown_params():
    d=DEMOS[0]
    with pytest.raises(ValueError,match='Unknown'):run_pipeline([ROOT/p for p in d['paths']],d['options'],d['scenario'],d['query'],{'invented':1})

def test_generic_temporal_query_uses_composite_evidence():
    d=DEMOS[2]
    out=run_pipeline([ROOT/p for p in d['paths']],d['options'],d['scenario'],'Compare the before and after images. What changed?')
    assert out['task']=='TEMPORAL_CHANGE_ANALYSIS'
    assert out['specialists'][0]['mode']=='temporal_change_analysis'
    assert out['specialists'][0]['temporal_evidence']['changed_fraction']>=0
    assert any(c['claim']['type']=='visible_change' for c in out['verification']['checks'])
    assert out['confidence_breakdown']['evidence_support'] is not None

def test_temporal_visible_change_does_not_certify_semantics():
    d=DEMOS[2]
    out=run_pipeline([ROOT/p for p in d['paths']],d['options'],d['scenario'],'What changed?')
    assert out['task']=='TEMPORAL_CHANGE_ANALYSIS'
    assert all(c['claim']['type']=='visible_change' for c in out['verification']['checks'])

def test_upload_report_and_websocket():
    d=DEMOS[1]
    with TestClient(app) as client:
        with (ROOT/d['paths'][0]).open('rb') as f:
            response=client.post('/api/jobs',files={'images':('image.tif',f,'image/tiff')},data={'query':d['query'],'options':json.dumps(d['options'])})
        key=response.json()['job_id'];events=[]
        with client.websocket_connect(f'/api/trace/{key}') as ws:
            while True:
                event=ws.receive_json()
                if event['type']=='trace':events.append(event['event'])
                else:break
        assert event['type']=='complete'
        out=event['result']
        if out is None:
            # WS may deliver 'complete' before the result dict is set due to async timing;
            # fall back to the REST polling endpoint which is guaranteed to have it.
            job_resp=client.get(f'/api/jobs/{key}')
            assert job_resp.status_code==200
            out=job_resp.json().get('result')
        assert out is not None,'Job result missing from both WebSocket and polling endpoint'
        assert out['overlay']['type'] in ('bbox','mask')
        assert len(events)==len(out['execution_trace'])
        report=client.get(out['report_url']);assert report.status_code==200
        assert report.json()==out
        assert client.get(out['previews'][0]).headers['content-type']=='image/png'

def test_invalid_bytes_return_error_trace():
    with TestClient(app) as c:
        r=c.post('/api/analyze',files={'images':('bad.tif',b'not raster')},data={'query':'What is visible?'})
        assert r.status_code==422
        assert r.json()['detail']['execution_trace'][-1]['action']=='error'

def test_specialists_independently_callable(monkeypatch):
    from models.service import app as service
    from gateway.validation import public_contract
    for module,demo in [('models.vqa_caption.model',DEMOS[0]),('models.grounding.model',DEMOS[1]),('models.change_vqa.model',DEMOS[2]),('models.fusion_optical_sar.model',DEMOS[3])]:
        monkeypatch.setenv('TOOL_MODULE',module)
        bundle=validate([ROOT/p for p in demo['paths']],demo['options'],demo['scenario'])
        payload={**public_contract(bundle),'images':[{k:v for k,v in i.items() if k!='array'} for i in bundle['images']]}
        r=TestClient(service).post('/run',json={'bundle':payload,'call':{'task':'VQA','image_ids':['img1'],'query':demo['query'],'params':{'threshold':.25}}})
        assert r.status_code==200,r.text
        assert 'claims' in r.json()
