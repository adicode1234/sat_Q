import hashlib,json
from pathlib import Path
import numpy as np
import pytest
import rasterio
from gateway.validation import read_image,validate,rgb
from models.water import inputs
from verification.engine import verify
from training.make_demo import write_tif
ROOT=Path(__file__).resolve().parents[1]

def test_radiometry_conversion_is_once_and_source_is_unchanged(tmp_path):
    path=tmp_path/'s2.tif';write_tif(path,np.full((5,32,32),2000,dtype='float32'),['blue','green','red','nir','swir'])
    before=hashlib.sha256(path.read_bytes()).hexdigest()
    image=read_image(path,'img1',{'reflectance_scale':.0001})
    assert np.allclose(image['array'],.2)
    assert image['preprocessing_steps'][0]['code']=='REFLECTANCE_CONVERSION'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==before
    with rasterio.open(path,'r+') as src:src.scales=[.0001]*5
    with pytest.raises(ValueError,match='second'):read_image(path,'img1',{'reflectance_scale':.0001})

def test_raw_dn_and_other_polarizations_do_not_enter_sar_model():
    a=np.ones((2,32,32),dtype='float32')
    s={'modality':'SAR','array':a,'bands':['vv','vh'],'sar_units':'unknown'}
    with pytest.raises(ValueError,match='unknown'):inputs([s],'sar')
    s.update(sar_units='db',bands=['hh','hv'])
    with pytest.raises(ValueError,match='VV and VH'):inputs([s],'sar')

def test_sar_power_units_produce_equivalent_model_inputs():
    a=np.random.default_rng(5).uniform(-24,-5,(2,32,32)).astype('float32')
    s={'modality':'SAR','array':a,'bands':['vv','vh'],'sar_units':'db'}
    log,valid,_=inputs([s],'sar');linear,_,_=inputs([{**s,'array':10**(a/10),'sar_units':'linear'}],'sar')
    assert np.allclose(log[valid],linear[valid],atol=1e-4)

def test_real_upload_never_gets_synthetic_landcover(monkeypatch,tmp_path):
    from models.vqa_caption.model import run
    monkeypatch.setenv('SATQUERY_USE_VILT','0')
    p=tmp_path/'rgb.tif';write_tif(p,np.random.default_rng(5).uniform(0,1,(3,32,32)).astype('float32'),['red','green','blue'])
    b=validate([p],[{}],'SINGLE');out=run(b,{'query':'Describe this image','task':'CAPTION'})
    assert 'fractions' not in out
    assert out['mode']=='real_image_capability_unavailable'

def test_missing_evidence_and_contradiction_are_distinct():
    b=validate([ROOT/'data/demo/optical_before.tif'],[{}],'SINGLE')
    out=verify(b,[{'neural_confidence':.8,'claims':[{'type':'water','fraction':.99},{'type':'unknown','value':'object'}]}])
    assert out['contradicted_claim_count']==1
    assert out['unverified_claim_count']==1
    assert out['checks'][0]['evidence_state']=='contradictory'
    assert out['checks'][1]['evidence_state']=='missing'

def test_rgb_display_preserves_natural_image_colors():
    image={'array':np.array([[[.2,.6]],[[.3,.7]],[[.4,.8]]]),'bands':['red','green','blue'],
           'source_type':'benchmark','raster_metadata':{'format':'PNG'}}
    assert np.array_equal(rgb(image),np.array([[[51,76,102],[153,178,204]]],dtype='uint8'))


def test_normalized_metadata_does_not_apply_quantification_twice(tmp_path):
    from gateway.normalization import materialize
    p=tmp_path/'scaled.tif';write_tif(p,np.full((5,32,32),2000,dtype='float32'),['blue','green','red','nir','swir'])
    with rasterio.open(p,'r+') as dst:dst.update_tags(QUANTIFICATION_VALUE='10000')
    b=validate([p],[{}],'SINGLE');materialize(b,tmp_path/'normalized')
    reread=read_image(b['images'][0]['path'],'img1',{})
    assert np.allclose(reread['array'],.2)


def test_api_accepts_explicit_radiometry_and_rejects_nonfinite():
    from gateway.app import ImageOptions
    from pydantic import ValidationError
    assert ImageOptions(sensor='Sentinel-2',reflectance_scale=.0001).reflectance_scale==.0001
    with pytest.raises(ValidationError):ImageOptions(reflectance_scale=float('nan'))


def test_verification_uses_model_valid_domain():
    from gateway.spatial import pack_mask
    from verification.engine import summaries
    b=validate([ROOT/'data/demo/optical_before.tif'],[{}],'SINGLE')
    _,maps=summaries(b);index=maps['img1']['NDWI'];valid=np.isfinite(index)&(index>.15)
    assert valid.any()
    out=verify(b,[{'neural_confidence':.5,'valid_mask':pack_mask(valid),
                  'claims':[{'type':'water','fraction':1.,'sampling_basis':'model_valid','model_valid_coverage':float(valid.mean())}]}])
    assert out['checks'][0]['agreement']==1


def test_change_mask_does_not_verify_itself(tmp_path):
    from PIL import Image
    p=tmp_path/'before.png';q=tmp_path/'after.png'
    a=np.random.default_rng(5).integers(0,255,(64,64,3),dtype='uint8');Image.fromarray(a).save(p);Image.fromarray(a).save(q)
    b=validate([p,q],[{'date':'2024-01-01'},{'date':'2024-02-01'}],'BITEMPORAL_PAIR')
    out=verify(b,[{'neural_confidence':.2,'claims':[{'type':'visible_change','fraction':.1}],
                  'temporal_evidence':{'evidence_strength':1,'changed_fraction':.1,'alignment_quality':'GOOD'}}])
    assert out['verification_coverage']==0
    assert out['symbolic_agreement'] is None
    assert out['trust_score']<.2
