"""Acceptance and safety coverage for automatic input normalization."""
import asyncio
import hashlib
import json
from pathlib import Path
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin, from_bounds
from rasterio.warp import transform_bounds
from PIL import Image
from fastapi.testclient import TestClient
from gateway.validation import validate, read_image
from gateway.errors import InputError
from gateway.normalization import materialize, band_name
from gateway.spatial import region_features
from gateway import settings


def tif(path, shape=(64,64), bands=('Red','Green','Blue'), crs='EPSG:32643', transform=None, data=None):
    data = np.random.default_rng(4).random((len(bands),*shape)).astype('float32') if data is None else data
    with rasterio.open(path,'w',driver='GTiff',width=shape[1],height=shape[0],count=len(bands),dtype='float32',
                       nodata=-9999,crs=crs,transform=transform or from_origin(650000,1450000,10,10)) as dst:
        dst.write(data);dst.descriptions=bands;dst.update_tags(source='acceptance fixture')
        for n in range(1,len(bands)+1):dst.update_tags(n,provenance=f'channel {n}')
    return path


def pair(paths, query='', options=None, scenario='BITEMPORAL_PAIR'):
    return validate(paths,options or [{'date':'2024-01-01'},{'date':'2024-02-01'}],scenario,query)


def test_river_dimensions_and_original_hashes(tmp_path):
    before=tif(tmp_path/'river_before.tif',(710,1600),crs='EPSG:4326',transform=from_bounds(77,12,77.16,12.071,1600,710))
    after=tif(tmp_path/'river_after.tif',(709,1600),crs='EPSG:4326',transform=from_bounds(77,12,77.16,12.071,1600,709))
    hashes=[hashlib.sha256(p.read_bytes()).hexdigest() for p in (before,after)]
    out=pair([before,after]);a,b=out['images']
    assert out['validation_status']=='READY_WITH_PREPROCESSING'
    assert b['shape']==a['shape']==[710,1600] and b['was_resampled']
    assert b['bands']==['red','green','blue']
    assert b['raster_metadata']['band_descriptions']==['Red','Green','Blue']
    materialize(out,tmp_path/'normalized')
    assert hashes==[hashlib.sha256(p.read_bytes()).hexdigest() for p in (before,after)]
    with rasterio.open(b['working_path']) as src:
        assert src.descriptions==('Red','Green','Blue')
        assert src.tags(1)['provenance']=='channel 1'
        assert src.tags()['source']=='acceptance fixture'


def test_different_valid_crs(tmp_path):
    a=tif(tmp_path/'a.tif')
    with rasterio.open(a) as src:bounds=transform_bounds(src.crs,'EPSG:4326',*src.bounds)
    b=tif(tmp_path/'b.tif',crs='EPSG:4326',transform=from_bounds(*bounds,64,64))
    out=pair([a,b]);x,y=out['images']
    assert y['was_reprojected'] and x['crs']==y['crs'] and x['transform']==y['transform']


@pytest.mark.parametrize('transform',[from_origin(650002,1450000,10,10),from_origin(650000,1450000,11,11)])
def test_transform_resolution_normalization(tmp_path,transform):
    out=pair([tif(tmp_path/'a.tif'),tif(tmp_path/'b.tif',transform=transform)])
    assert out['images'][0]['transform']==out['images'][1]['transform']
    assert out['images'][1]['was_resampled']


def test_rgb_bgr_mapping_and_derivative(tmp_path):
    data=np.random.default_rng(6).random((3,64,64)).astype('float32')
    out=pair([tif(tmp_path/'a.tif',data=data),tif(tmp_path/'b.tif',bands=('Blue','Green','Red'),data=data[::-1])])
    assert np.array_equal(out['images'][0]['array'],out['images'][1]['array'])
    assert out['images'][1]['was_band_reordered']
    materialize(out,tmp_path/'normalized')
    with rasterio.open(out['images'][1]['path']) as src:assert src.descriptions==('Red','Green','Blue')


def test_known_options_restore_missing_descriptions(tmp_path):
    paths=[tif(tmp_path/'a.tif'),tif(tmp_path/'b.tif',shape=(63,64),bands=(None,None,None))]
    out=pair(paths,options=[{'date':'2024-01-01'},{'date':'2024-02-01','bands':['red','green','blue']}])
    materialize(out,tmp_path/'normalized')
    with rasterio.open(out['images'][1]['path']) as src:assert src.descriptions==('red','green','blue')


@pytest.mark.parametrize('extension',['png','jpg','jpeg'])
def test_ordinary_visual_single(tmp_path,extension):
    p=tmp_path/f'photo.{extension}';Image.new('RGB',(64,64),(40,100,80)).save(p)
    out=validate([p],[{}],'SINGLE');image=out['images'][0]
    assert out['validation_status']=='READY_WITH_LIMITATIONS'
    assert image['visual_only'] and not image['geospatial_measurements_allowed']
    assert region_features(image,np.ones((64,64),bool))['status']=='UNAVAILABLE'


def test_visual_temporal_translation(tmp_path):
    data=np.random.default_rng(3).integers(0,255,(128,128,3),dtype='uint8')
    paths=[tmp_path/'a.png',tmp_path/'b.png']
    Image.fromarray(data).save(paths[0]);Image.fromarray(np.roll(data,3,axis=1)).save(paths[1])
    out=pair(paths);a,b=out['images']
    assert b['was_coregistered'] and not a['geospatial_measurements_allowed']
    valid=np.isfinite(b['array']).all(0)
    assert np.array_equal(a['array'][:,valid],b['array'][:,valid])
    assert out['validation']['alignment'][0]['overlap_valid_fraction']>.9


def test_unrelated_visual_pair_rejected(tmp_path):
    paths=[tmp_path/'a.png',tmp_path/'b.png']
    for n,p in enumerate(paths):Image.fromarray(np.random.default_rng(n).integers(0,255,(64,64,3),dtype='uint8')).save(p)
    with pytest.raises(InputError,match='alignment'):pair(paths)


def test_valid_georeference(tmp_path):
    image=read_image(tif(tmp_path/'geo.tif'),'img1',{})
    assert image['geospatial_measurements_allowed'] and not image['visual_only']


def test_temporal_modality_suggests_fusion(tmp_path):
    paths=[tif(tmp_path/'a.tif'),tif(tmp_path/'sar.tif',bands=('vv',))]
    with pytest.raises(InputError) as error:pair(paths,options=[{}, {'modality':'SAR'}])
    assert error.value.code=='MODALITY_MISMATCH' and 'Optical + SAR' in error.value.suggestion


def test_fusion_unknown_sar_partial_overlap(tmp_path):
    paths=[tif(tmp_path/'a.tif'),tif(tmp_path/'sar.tif',bands=('vv',),transform=from_origin(650100,1450000,10,10))]
    out=pair(paths,options=[{}, {'modality':'SAR'}],scenario='CROSS_MODAL_PAIR')
    assert out['images'][0]['shape']==out['images'][1]['shape']==[64,54]
    assert any('UNCALIBRATED' in n for n in out['validation']['warnings'])
    from verification.engine import summaries
    assert 'SAR' not in summaries(out)[1]['img2']


def test_no_overlap(tmp_path):
    with pytest.raises(InputError) as error:pair([tif(tmp_path/'a.tif'),tif(tmp_path/'b.tif',transform=from_origin(800000,1450000,10,10))])
    assert error.value.code=='NO_SPATIAL_OVERLAP'


def test_partial_overlap_masks_both_dates(tmp_path):
    out=pair([tif(tmp_path/'a.tif'),tif(tmp_path/'b.tif',transform=from_origin(650100,1450000,10,10))])
    a,b=out['images']
    assert np.array_equal(np.isfinite(a['array']),np.isfinite(b['array']))
    assert np.isfinite(a['array'][0]).sum()==64*54


@pytest.mark.parametrize('query,unavailable',[('What visually changed?',[]),('Measure NDVI',['NDVI'])])
def test_task_aware_common_bands(tmp_path,query,unavailable):
    out=pair([tif(tmp_path/'a.tif'),tif(tmp_path/'b.tif',bands=('Red','Green','Blue','NIR'))],query)
    assert out['images'][1]['bands']==['red','green','blue']
    assert out['validation']['unavailable_tasks']==unavailable
    if unavailable:
        from models.measurement import run
        assert run(out,{'query':query})['mode']=='measurement_unavailable'


@pytest.mark.parametrize('count',[3,9,20])
def test_multidate_limit_and_normalization(tmp_path,count):
    paths=[tif(tmp_path/f'{n}.tif',shape=(64-n%2,64)) for n in range(count)]
    out=validate(paths,[{'date':f'2024-01-{n+1:02}'} for n in range(count)],'MULTI_DATE')
    assert len(out['images'])==count and all(i['shape']==[64,64] for i in out['images'])


def test_limits_are_structured():
    settings.check_size(127*1024**2)
    with pytest.raises(InputError) as error:settings.check_size(129*1024**2)
    assert error.value.as_dict()['blocking_errors'][0]['code']=='FILE_TOO_LARGE'
    settings.check_count('MULTI_DATE',20)
    with pytest.raises(InputError):settings.check_count('MULTI_DATE',21)
    assert settings.query_text('  '+'x'*7000+'  ')=='x'*7000
    with pytest.raises(InputError) as error:settings.query_text('x'*8001)
    assert error.value.code=='QUERY_LENGTH_EXCEEDED'


def test_placeholder_area_disabled(tmp_path):
    out=validate([tif(tmp_path/'fake.tif',crs='EPSG:4326',transform=from_bounds(0,0,1,1,64,64))],[{}],'SINGLE')
    image=out['images'][0]
    assert image['visual_only'] and image['crs']=='EPSG:4326'
    assert region_features(image,np.ones((64,64),bool))['status']=='UNAVAILABLE'


def test_preprocessing_failure_is_structured(tmp_path,monkeypatch):
    def broken(*a,**kw):raise RuntimeError('warp failed')
    monkeypatch.setattr('gateway.normalization.reproject',broken)
    with pytest.raises(InputError) as error:pair([tif(tmp_path/'a.tif'),tif(tmp_path/'b.tif',shape=(63,64))])
    assert error.value.code=='PREPROCESSING_FAILED' and 'untouched' in str(error.value)


def test_preprocessing_trace(tmp_path,monkeypatch):
    from controller.pipeline import run_pipeline
    monkeypatch.setenv('SATQUERY_USE_CHANGE_MODEL','0')
    paths=[tif(tmp_path/'a.tif'),tif(tmp_path/'b.tif',shape=(63,64))]
    result=run_pipeline(paths,[{'date':'2024-01-01'},{'date':'2024-02-01'}],'BITEMPORAL_PAIR','Where is the change mask?')
    steps=result['input']['validation']['preprocessing_steps']
    events=[e['result'] for e in result['execution_trace'] if e['action']=='automatic_preprocessing']
    assert steps==events and any(e['code']=='RESAMPLED_TO_REFERENCE_GRID' for e in events)
    from gateway.app import remove_normalized
    remove_normalized(result['query_id'])


def test_inspection_and_request_errors(tmp_path):
    from gateway.app import app
    p=tmp_path/'photo.png';Image.new('RGB',(64,64),(20,80,50)).save(p)
    with TestClient(app) as client:
        assert client.get('/api/config').json()['max_upload_mb']==128
        response=client.post('/api/inspect',files={'images':('photo.png',p.read_bytes())})
        assert response.json()['validation_status']=='READY_WITH_LIMITATIONS'
        response=client.post('/api/jobs',files={'images':('photo.png',p.read_bytes())},data={'query':'x'*8001})
        assert response.status_code==422 and response.json()['detail']['code']=='QUERY_LENGTH_EXCEEDED'


def test_numeric_band_alias_requires_sensor_context():
    assert band_name('B4')=='b4'
    assert band_name('B4',{'sensor':'Sentinel-2'})=='red'
    assert band_name('B4',{'sensor':'Landsat 8'})=='b4'


def test_masked_scaled_derivative_roundtrip(tmp_path):
    a=tif(tmp_path/'a.tif');b=tif(tmp_path/'b.tif',shape=(63,64))
    with rasterio.open(b,'r+') as dst:
        dst.scales=(2,2,2);dst.offsets=(.1,.1,.1)
        data=dst.read();data[:,10:15,10:15]=-9999;dst.write(data)
    out=pair([a,b]);materialize(out,tmp_path/'normalized')
    image=out['images'][1];loaded=read_image(image['path'],'img2',{})
    np.testing.assert_allclose(loaded['array'],image['array'],equal_nan=True)


def test_upload_actual_size_boundaries(tmp_path):
    from gateway.app import uploads, remove_uploads
    from fastapi import UploadFile, HTTPException
    p=tif(tmp_path/'large.tif')
    for mb in (127,129):
        with p.open('r+b') as handle:handle.truncate(mb*1024**2)
        async def upload():
            with p.open('rb') as handle:
                return await uploads([UploadFile(filename='large.tif',file=handle)],'[{}]')
        if mb==127:
            paths,_=asyncio.run(upload())
            try:assert paths[0].stat().st_size==127*1024**2
            finally:remove_uploads(paths)
        else:
            with pytest.raises(HTTPException) as error:asyncio.run(upload())
            assert error.value.status_code==413 and error.value.detail['code']=='FILE_TOO_LARGE'


def test_multidate_21_structured_api_error(tmp_path):
    from gateway.app import app
    with TestClient(app) as client:
        response=client.post('/api/inspect',files=[('images',(f'{n}.png',b'x')) for n in range(21)],
                             data={'scenario':'MULTI_DATE','options':json.dumps([{}]*21)})
    assert response.status_code==422
    assert response.json()['detail']['status']=='INCOMPATIBLE'


def test_normalization_can_be_disabled(tmp_path,monkeypatch):
    monkeypatch.setenv('SATQUERY_AUTO_RESAMPLE','0')
    with pytest.raises(InputError) as error:pair([tif(tmp_path/'a.tif'),tif(tmp_path/'b.tif',shape=(63,64))])
    assert error.value.code=='GRID_NORMALIZATION_DISABLED'


def test_unknown_sar_relative_summary(tmp_path):
    from models.vqa_caption.model import run
    out=validate([tif(tmp_path/'sar.tif',bands=('vv',))],[{'modality':'SAR'}],'SINGLE')
    result=run(out,{'query':'Describe the image','task':'CAPTION'})
    assert 'relative visual summary' in result['answer'] and result['claims']==[]
    assert result['neural_confidence']==0
