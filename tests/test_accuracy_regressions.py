import json
from pathlib import Path
import numpy as np
import pytest
from models.vqa_caption.model import normalize_vilt_query
from controller.scene_analyzer import analyze_water_morphology,connected_regions,generate_scene_inventory

@pytest.mark.parametrize('question',['How many buildings are there?','What color is the river?','Are there no roads in this image?','Which side has more trees?'])
def test_semantic_question_is_preserved(question):
    assert normalize_vilt_query(question)==question

def test_thin_river_is_not_dropped_by_stride_or_area_percentage():
    mask=np.zeros((512,512),bool);mask[:,251]=True
    result=analyze_water_morphology(mask)
    assert result['has_water'] and result['has_river']
    assert result['components'][0]['area']==512
    assert result['components'][0]['box']==[251,0,252,512]

def test_connected_components_count_every_pixel_once():
    mask=np.zeros((20,30),bool);mask[1:4,2:8]=True;mask[8:12,20:25]=True
    components=connected_regions(mask)
    assert len(components)==2
    assert sum(c[4] for c in components)==int(mask.sum())

def test_nodata_does_not_dilute_composition(monkeypatch):
    torch = pytest.importorskip('torch', reason='PyTorch not installed')
    import models.rgb_water as rgb
    class Dummy:
        def __call__(self,pixel_values):
            from types import SimpleNamespace
            logits=torch.full((1,6,*pixel_values.shape[-2:]),-10.)
            logits[:,1]=10
            return SimpleNamespace(logits=logits)
    monkeypatch.setattr(rgb,'get_model',lambda:Dummy())
    a=np.full((3,32,32),.3,dtype='float32');a[:,:,:16]=np.nan
    image={'id':'img1','bands':['red','green','blue'],'modality':'optical','array':a,'shape':[32,32],'source_type':'synthetic_demo'}
    mapped,p,stats,valid=rgb.predict_segmentation(image)
    assert stats['water']==100
    assert not valid[:,:16].any()
    assert np.isnan(p[:,:16]).all()
    assert not mapped[:,:16].any()

def test_small_water_candidate_is_not_reported_as_absent(monkeypatch):
    import controller.scene_analyzer as scene
    mask=np.zeros((100,100),bool);mask[:,50]=True
    monkeypatch.setattr(scene,'_analyze_single_image',lambda i:{'w_mask':mask,'v_mask':~mask,'b_mask':np.zeros_like(mask),'road_mask':np.zeros_like(mask),'stats':{'water':1.,'veg':99.,'built':0.,'road':0.,'other':0.},'mode':'test','valid':np.ones_like(mask)})
    out=generate_scene_inventory({'images':[{'id':'img1'}],'scenario':'SINGLE'},[],'Where is the river?',{'answer':'candidate','trust_score':.2})
    assert out['has_water']
    assert '1.0%' in out['answer']
    assert 'confirmed' not in out['answer'].lower()
    assert not any(a.get('category') == 'water' for a in out['absent'])


def test_png_scaling_is_not_treated_as_reflectance():
    from models.rgb_water import pixels
    a=np.full((3,32,32),.2,dtype='float32')
    image={'modality':'optical','bands':['red','green','blue'],'array':a,'raster_metadata':{'format':'PNG'},'radiometry':{'reflectance_scale_known':True}}
    assert np.allclose(pixels(image)[0],51)


def test_filename_does_not_invent_geography(tmp_path):
    from PIL import Image
    from gateway.validation import read_image
    p=tmp_path/'before_kolkata.png';Image.fromarray(np.full((32,32,3),128,dtype='uint8')).save(p)
    image=read_image(p,'img1',{})
    assert image['geo_bounds'] is None
    assert not image['georeferenced']
