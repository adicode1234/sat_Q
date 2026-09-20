import numpy as np
import pytest
from gateway.validation import validate
from models.vqa_caption.model import run,CHECKPOINT
from models.features import pixel_predictions
from models.change_vqa.model import run as change
from verification.engine import verify
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def bundle():return validate([ROOT/'data/demo/optical_before.tif'],[{'modality':'optical'}],'SINGLE')

def test_every_spoken_landcover_claim_is_verified(monkeypatch):
    monkeypatch.delenv('SATQUERY_USE_VILT',raising=False)
    b=bundle();out=run(b,{'task':'VQA','query':'Where is water?'})
    assert {c['type'] for c in out['claims']}=={'water','vegetation','built_up'}
    assert len(verify(b,[out])['checks'])==3

def test_nodata_never_becomes_a_landcover_class(monkeypatch):
    monkeypatch.delenv('SATQUERY_USE_VILT',raising=False)
    b=bundle();b['images'][0]['array'][:,:,:128]=np.nan
    mask,_,_=pixel_predictions(b['images'][0],CHECKPOINT)
    assert (mask[:,:128]==-1).all()
    out=run(b,{'task':'CAPTION','query':'Describe the scene'})
    assert sum(out['fractions'].values())==pytest.approx(1)
    assert '50.0%' in out['answer']

def test_sparse_spectral_data_cannot_verify_whole_rgb_image(monkeypatch):
    monkeypatch.delenv('SATQUERY_USE_VILT',raising=False)
    b=bundle();out=run(b,{'task':'VQA','query':'Water?'})
    b['images'][0]['array'][3,:,20:]=np.nan
    checked=verify(b,[out])
    assert checked['symbolic_agreement'] is None
    assert checked['verification_coverage']==0

def test_small_extent_disagreement_is_not_hidden():
    b=bundle();check=verify(b,[{'neural_confidence':.5,'claims':[{'type':'water','fraction':0,'image_id':'img1'}]}])
    assert check['checks'][0]['status']=='disagrees'

def test_disjoint_temporal_coverage_rejected():
    b=bundle();a=b['images'][0];c={**a,'array':a['array'].copy()};a['array'][:,:,:128]=np.nan;c['array'][:,:,128:]=np.nan
    with pytest.raises(ValueError,match='no shared valid pixels'):change({'images':[a,c]},{'params':{'threshold':.25}})

def test_unnamed_bands_do_not_produce_fake_rgb_landcover():
    b=bundle();b['images'][0]['bands']=['b1','b2','b3','b4','b5']
    assert run(b,{'task':'VQA','query':'What is visible?'})['claims']==[]

def test_trained_change_model_is_loaded_and_disclosed(monkeypatch):
    import json
    pytest.importorskip('torch')
    monkeypatch.setenv('SATQUERY_USE_CHANGE_MODEL','1')
    sample=next(s for s in json.loads((ROOT/'evaluation/samples.json').read_text()) if s['dataset']=='CDVQA')
    b=validate([ROOT/p for p in sample['paths']],sample['options'],sample['scenario'])
    out=change(b,{'query':sample['query'],'params':{'threshold':.25}})
    assert out['mode'].startswith('cdvqa_tiny_siamese_vqa')
    assert out['short_answer']
    assert 'two training image pairs' in out['training_scope']
    assert any(c['type']=='change_vqa_answer' for c in out['claims'])


def test_sar_single_measurements_do_not_self_verify():
    b=validate([ROOT/'data/demo/sar.tif'],[{'modality':'SAR','sar_units':'db'}],'SINGLE')
    out=run(b,{'task':'VQA','query':'Is there water?'})
    assert out['mode']=='deterministic_sar_measurement_vqa'
    assert 'cannot uniquely identify water' in out['answer']
    checked=verify(b,[out])
    assert checked['trust_score']==0
    assert checked['symbolic_agreement'] is None
