import json
from pathlib import Path
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from PIL import Image
from gateway.validation import validate, read_image

ROOT=Path(__file__).resolve().parents[1]


def raster(path, data=None, crs='EPSG:32643', transform=None, bands=None):
    data = np.arange(1024,dtype='float32').reshape(1,32,32)/1024 if data is None else data
    with rasterio.open(path,'w',driver='GTiff',width=data.shape[2],height=data.shape[1],count=len(data),dtype='float32',
                       crs=crs,transform=transform or from_origin(650000,1450000,10,10),nodata=-9999) as dst:
        dst.write(data)
        for n,b in enumerate(bands or ['red']*len(data),1): dst.set_band_description(n,b)
        dst.update_tags(ACQUISITION_DATE='2024-01-02')
    return path


def test_raster_metadata_scale_and_hash(tmp_path):
    path=raster(tmp_path/'real.tif')
    with rasterio.open(path,'r+') as dst: dst.scales=[2]; dst.offsets=[.1]
    image=read_image(path,'img1',{})
    assert image['raster_metadata']['dtype']==['float32']
    assert image['raster_metadata']['bounds']
    assert image['array'][0,0,0]==pytest.approx(.1)
    assert image['date']=='2024-01-02'
    assert image['source_type']=='operational_geospatial'
    assert len(image['sha256'])==64


def test_no_geography_in_plain_tiff(tmp_path):
    image=read_image(raster(tmp_path/'plain.tif',crs=None),'img1',{})
    assert not image['georeferenced']
    assert image['raster_metadata']['bounds'] is None


def test_modality_mismatch(tmp_path):
    path=raster(tmp_path/'ndvi.tif',bands=['NDVI'])
    with pytest.raises(ValueError,match='MODALITY MISMATCH'):
        validate([path],[{'modality':'SAR'}],'SINGLE')


@pytest.mark.parametrize('extension',['png','jpg'])
def test_benchmark_formats(tmp_path,extension):
    path=tmp_path/('fixture.'+extension)
    Image.new('RGB',(32,32),(20,70,10)).save(path)
    assert validate([path],[{}],'SINGLE')['images'][0]['visual_only']
    out=validate([path],[{'benchmark_source':'test fixture'}],'SINGLE')
    assert out['images'][0]['source_type']=='benchmark'
    assert out['validation_status']=='READY_WITH_LIMITATIONS'


def test_signature_and_no_fake_sar_calibration(tmp_path):
    path=tmp_path/'bad.tif';path.write_bytes(b'not a tiff')
    with pytest.raises(ValueError,match='signature'): read_image(path,'img1',{})
    path=raster(tmp_path/'sar.tif',bands=['vv'])
    out=validate([path],[{'modality':'SAR'}],'SINGLE')
    assert out['images'][0]['calibration_state']=='unknown'
    assert any('calibration' in r['message'] for r in out['validation']['reasons'])


def test_quality_reflects_nodata(tmp_path):
    data=np.ones((1,32,32),dtype='float32');data[:,:,:24]=-9999
    image=read_image(raster(tmp_path/'poor.tif',data),'img1',{})
    assert image['quality']['valid_fraction']==.25
    assert image['quality']['score']<.25


def test_lossless_mask_and_equal_area(tmp_path):
    from gateway.spatial import pack_mask,unpack_mask,region_features
    image=read_image(raster(tmp_path/'geo.tif'),'img1',{})
    mask=np.zeros((32,32),dtype=bool);mask[5:15,5:15]=True
    assert np.array_equal(unpack_mask(pack_mask(mask)),mask)
    output=region_features(image,mask)
    assert output['area_m2']==pytest.approx(10000,rel=.01)
    assert output['area_ha']==pytest.approx(1,rel=.01)
    coords=output['features'][0]['geometry']['coordinates'][0]
    assert all(-180<=x<=180 and -90<=y<=90 for x,y in coords)
    image['georeferenced']=False
    assert region_features(image,mask)['status']=='UNAVAILABLE'


def test_geographic_area_is_not_degrees_squared(tmp_path):
    from gateway.spatial import region_features
    image=read_image(raster(tmp_path/'latlon.tif',crs='EPSG:4326',transform=from_origin(77,13,.0001,.0001)),'img1',{})
    area=region_features(image,np.ones((32,32),bool))['area_m2']
    assert 100000<area<140000


def test_html_escapes_query_and_contains_evidence():
    from gateway.reporting import render_html
    result={'query_id':'a'*32,'query':'<script>alert(1)</script>','answer':'ok','input':{},'specialists':[],
            'verification':{},'limitations':[],'execution_trace':[]}
    text=render_html(result)
    assert '<script>' not in text
    assert '&lt;script&gt;' in text
    assert 'MODEL INFERENCE' in text and 'PHYSICAL EVIDENCE' in text


def test_alignment_estimates_known_shift():
    from gateway.alignment import estimate_pair
    rng=np.random.default_rng(4);a=rng.normal(size=(1,64,64)).astype('float32')
    first={'array':a,'shape':[64,64],'modality':'optical'}
    second={**first,'array':np.roll(a,5,axis=2)}
    out=estimate_pair(first,second)
    assert abs(out['estimated_shift_pixels']['x'])==5
    assert out['score']>.5


def test_confidence_refusal_and_malformed_scores():
    from verification.confidence import normalize_score,decision
    for score in (float('nan'),-1,2,True):
        with pytest.raises(ValueError):normalize_score(score)
    v={'neural_confidence':0,'verification_coverage':0,'trust_score':0}
    assert decision(v,1,[], 'insufficient evidence')['status']=='MODEL_FAILURE'
    assert decision(v,.1,[{}], 'insufficient evidence')['status']=='INSUFFICIENT_EVIDENCE'
    assert decision({**v,'neural_confidence':.2},1,[{}],'insufficient evidence')['status']=='LOW_TRUST'


def test_roi_transform_and_measurement_trend(tmp_path):
    from gateway.regions import crop_bundle
    from models.measurement import run
    data=np.ones((2,32,32),dtype='float32');data[0]=.8;data[1]=.1
    paths=[raster(tmp_path/f't{i}.tif',data=data,bands=['green','nir']) for i in range(3)]
    options=[{'date':f'2024-0{i+1}-01'} for i in range(3)]
    bundle=validate(paths,options,'MULTI_DATE')
    crop=crop_bundle(bundle,{'box':[2,3,12,13]})
    assert crop['images'][0]['array'].shape==(2,10,10)
    assert crop['images'][0]['transform'][2]==650020
    assert crop['images'][0]['transform'][5]==1449970
    out=run(bundle,{'query':'water trend'})
    assert len(out['measurements'])==3
    assert out['trend']['direction']=='approximately stable'


@pytest.mark.parametrize('query,scenario,task',[
    ('What is visible?','SINGLE','VQA'),('Describe the scene','SINGLE','CAPTION'),
    ('Highlight water','SINGLE','GROUNDING'),('Locate buildings','SINGLE','GROUNDING'),
    ('What changed before and after?','BITEMPORAL_PAIR','TEMPORAL_CHANGE_ANALYSIS'),
    ('Compare optical and SAR','CROSS_MODAL_PAIR','FUSION_ANALYSIS'),
    ('Measure area','SINGLE','MEASUREMENT'),('Water trend','MULTI_DATE','TREND')])
def test_intent_registry(query,scenario,task):
    import yaml
    from controller.pipeline import RegistryClassifier
    registry=yaml.safe_load((ROOT/'configs/tool_registry.yaml').read_text())['tools']
    assert RegistryClassifier().classify({'scenario':scenario,'images':[{'modality':'optical'}]},query,registry)[0]==task


def test_labeled_spatial_metrics():
    from evaluation.metrics import mask_metrics,box_iou
    assert box_iou([0,0,10,10],[5,0,15,10])==pytest.approx(1/3)
    metrics=mask_metrics([[1,1],[0,0]],[[1,0],[0,0]])
    assert metrics['iou']==.5 and metrics['precision']==.5 and metrics['recall']==1
