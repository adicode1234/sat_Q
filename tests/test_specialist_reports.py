"""Behavior categories use mock output for orchestration, never model accuracy claims."""
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from controller.specialist_policy import route
from gateway.analysis_report import normalize
from gateway.errors import InputError

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = json.loads((Path(__file__).with_name('specialist_query_families.json')).read_text())
DEMOS = json.loads((ROOT/'data/demo/manifest.json').read_text())

@pytest.fixture(autouse=True)
def named_pipeline(monkeypatch):
    monkeypatch.setenv('SATQUERY_PIPELINE', 'specialists')
    for name in ('GEOCHAT','TEOCHAT','EARTHMIND'):
        monkeypatch.delenv(f'SATQUERY_{name}_RUNTIME', raising=False)


def bundle(name='GeoChat'):
    scenario = {'GeoChat':'SINGLE','TEOChat':'BITEMPORAL_PAIR','EarthMind':'CROSS_MODAL_PAIR'}[name]
    images = [{'id':'img1','modality':'optical'}]
    if name != 'GeoChat': images.append({'id':'img2','modality':'SAR' if name=='EarthMind' else 'optical'})
    return {'scenario':scenario,'images':images,'validation_status':'READY_WITH_LIMITATIONS', 'validation':{'warnings':[]}}


@pytest.mark.parametrize('name,question',[(n,q) for n,qs in FAMILIES.items() for q in qs])
def test_54_query_families(name, question):
    b=bundle(name)
    if name=='GeoChat' and 'increased' in question:
        with pytest.raises(InputError,match='one image'):route(b,question)
    else:
        assert route(b,question)[1]==name


@pytest.mark.parametrize('question',['What changed?','Were buildings demolished?','What appeared in the second image?','What is different now?','Has urban area grown?'])
def test_missing_temporal_image(question):
    with pytest.raises(InputError):route(bundle(),question)


@pytest.mark.parametrize('modality',['optical','SAR'])
def test_missing_sensor(modality):
    b=bundle();b['images'][0]['modality']=modality
    with pytest.raises(InputError,match='requires'):route(b,'Compare optical and SAR')


def raw(name='GeoChat', **kwargs):
    return {'specialist':name,'model':'test-runtime-only','answer':'The supplied evidence is inconclusive.',**kwargs}


def test_normalizer_does_not_add_findings_or_confidence():
    r=normalize(raw(),bundle(),'This is definitely urban, right?','VQA','GeoChat',[])
    assert r['answer']==raw()['answer']
    assert r['observations']==r['spatial_evidence']==[]
    assert r['confidence']['level'] is None
    assert not any(r['evidence'].values())
    assert r['execution_summary']['models_tools']==['test-runtime-only']


def test_earthmind_requires_actual_sar_section_not_mention():
    r=normalize(raw('EarthMind',answer='SAR and optical agree.'),bundle('EarthMind'),'Analyze both','FUSION_ANALYSIS','EarthMind',[])
    assert not r['evidence']['sar'] and not r['evidence']['agreement']
    assert any('SAR-specific' in u for u in r['uncertainty'])
    assert r['confidence']['level'] is None


def test_separate_evidence_is_lossless():
    e={'optical':[{'text':'Test optical evidence','image_ids':['img1'],'kind':'uncertain'}],
       'sar':[{'text':'Test radar evidence','image_ids':['img2'],'kind':'observed'}]}
    r=normalize(raw('EarthMind',evidence=e),bundle('EarthMind'),'Analyze','FUSION_ANALYSIS','EarthMind',[])
    assert r['evidence']['sar']==e['sar']
    assert not r['evidence']['agreement']


@pytest.mark.parametrize('data',[
    {'answer':''}, {'answer': '  '}, {'specialist':'EarthMind'}, {'answer':123},
    {'evidence':{'sar':[{'text':'No support','image_ids':['img1']}]}},
    {'evidence':{'general':[{'text':'No support','image_ids':['img9']}]}},
    {'evidence':{'before':[{'text':'No support','image_ids':['img1']}]}},
    {'observations':[{'text':'No support','image_ids':['img9']}]},
    {'confidence':{'level':'high','score':.99}}, {'overlay':{'data':[[1]]}},
])
def test_malformed_or_wrong_source_output_rejected(data):
    with pytest.raises(ValueError):normalize(raw(**data),bundle(),'Describe','VQA','GeoChat',[])


def test_runtime_missing_fails_honestly_without_cloud(monkeypatch):
    from controller.pipeline import run_pipeline
    from models import cloud_vision
    monkeypatch.setattr(cloud_vision,'enabled',lambda:True)
    d=DEMOS[0]
    r=run_pipeline([ROOT/p for p in d['paths']],d['options'],d['scenario'],'Describe this image')
    assert r['decision']['code']=='MODEL_UNAVAILABLE'
    assert r['specialists']==[] and r['execution_summary']['models_tools']==[]
    assert r['trust_score'] is None
    assert 'GeoChat unavailable' in r['answer']


@pytest.mark.parametrize('index,name',[(0,'GeoChat'),(2,'TEOChat'),(3,'EarthMind')])
def test_pipeline_runtime_contract_and_policies(monkeypatch,index,name):
    from controller.pipeline import run_pipeline
    import models.specialist_runtime as runtime
    calls=[]
    def run(b,c):
        calls.append(c)
        return raw(name)
    monkeypatch.setenv(f'SATQUERY_{name.upper()}_RUNTIME','unit_test_runtime')
    original=runtime.importlib.import_module
    monkeypatch.setattr(runtime.importlib,'import_module',lambda name:SimpleNamespace(run=run) if name=='unit_test_runtime' else original(name))
    d=DEMOS[index]
    r=run_pipeline([ROOT/p for p in d['paths']],d['options'],d['scenario'],'Give me a full analysis')
    assert r['answer']==raw(name)['answer']
    assert r['specialist']==name and r['execution_summary']['processing_status']=='completed'
    assert 'independently' in calls[0]['response_policy']
    assert calls[0]['query']=='Give me a full analysis'
    assert len(calls[0]['image_ids'])==len(d['paths'])
    assert r['specialists'][0]['raw_output']==raw(name)


def test_api_failure_report_export_and_health():
    from fastapi.testclient import TestClient
    from gateway.app import app
    d=DEMOS[0]
    with TestClient(app) as client:
        health=client.get('/api/health').json()
        assert not health['all_specialists_ready']
        with (ROOT/d['paths'][0]).open('rb') as f:
            response=client.post('/api/analyze',files={'images':('input.tif',f,'image/tiff')},data={'query':'Describe image','options':json.dumps(d['options'])})
        assert response.status_code==200,response.text
        result=response.json()
        assert result['decision']['status']=='MODEL_FAILURE'
        assert client.get(result['report_url']).json()['analysis_report']==result['analysis_report']
        html=client.get(result['html_report_url']).text
        assert 'Unavailable' not in html or 'unavailable' in html.lower()
        assert '94%' not in html and 'AI Visual Accuracy' not in html
        assert 'Original image' in html


def test_corrupt_upload_before_runtime(monkeypatch):
    from fastapi.testclient import TestClient
    from gateway.app import app
    import models.specialist_runtime as runtime
    def forbidden(*args):raise AssertionError('Inference must not run')
    monkeypatch.setattr(runtime,'run',forbidden)
    r=TestClient(app).post('/api/analyze',files={'images':('bad.png',b'bad bytes')},data={'query':'Describe'})
    assert r.status_code==422


def test_actual_grounding_boundary_preserves_tool_output(monkeypatch):
    from controller.pipeline import run_pipeline
    import models.specialist_runtime as runtime
    from models.grounding import dino
    monkeypatch.setattr(runtime, 'run', lambda b,c:raw())
    monkeypatch.setenv('SATQUERY_USE_DINO','1')
    boxes=[{'box':[1,2,8,9],'label':'test object','score':.4}]
    monkeypatch.setattr(dino,'detect',lambda *args:boxes)
    d=DEMOS[0]
    r=run_pipeline([ROOT/p for p in d['paths']],d['options'],d['scenario'],'Locate a building')
    assert r['overlay']['data']==boxes
    assert r['answer']==raw()['answer']
    assert r['spatial_evidence'][0]['source']=='Grounding DINO'
    assert r['confidence']['level'] is None


def test_incompatible_cross_modal_pair_is_blocked_before_inference(tmp_path, monkeypatch):
    from controller.pipeline import run_pipeline
    import models.specialist_runtime as runtime
    from PIL import Image
    import numpy as np
    def forbidden(*args):raise AssertionError('Inference must not run')
    monkeypatch.setattr(runtime,'run',forbidden)
    p=tmp_path/'optical.png';q=tmp_path/'radar.png'
    Image.fromarray(np.random.default_rng(3).integers(0,255,(64,64,3),dtype='uint8')).save(p)
    Image.fromarray(np.random.default_rng(4).integers(0,255,(64,64),dtype='uint8')).save(q)
    with pytest.raises(InputError):
        run_pipeline([p,q],[{'modality':'optical'},{'modality':'SAR'}],'CROSS_MODAL_PAIR','Analyze the pair')


def test_failed_normalization_does_not_publish_raw_output(monkeypatch):
    from controller.pipeline import run_pipeline
    import models.specialist_runtime as runtime
    monkeypatch.setattr(runtime,'run',lambda *args:raw(answer={'secret':'must not appear'}))
    d=DEMOS[0]
    r=run_pipeline([ROOT/p for p in d['paths']],d['options'],d['scenario'],'Describe')
    assert r['decision']['code']=='MALFORMED_MODEL_OUTPUT'
    assert 'must not appear' not in json.dumps(r)
