import asyncio
from copy import deepcopy
from unittest.mock import patch
import numpy as np
import pytest
from rasterio.transform import from_origin
from gateway.regions import crop_bundle, geographic_box
from gateway.errors import InputError


def bundle():
    return {'images':[{'id':'img1','array':np.ones((3,100,100)), 'shape':[100,100],
        'bands':['red','green','blue'],'modality':'optical', 'crs':'EPSG:4326',
        'transform':list(from_origin(10,20,.1,.1))[:6]}], 'validation':{},'metadata':{}}


def test_map_rectangle_maps_to_source_pixels():
    assert geographic_box(bundle(),[11,12,14,18]) == [10,20,40,80]


@pytest.mark.parametrize('bounds', [[9,12,14,18],[14,12,11,18],[11,float('nan'),14,18],[179,12,-179,18]])
def test_invalid_map_rectangles_rejected(bounds):
    with pytest.raises(InputError): geographic_box(bundle(),bounds)


def test_missing_georeference_rejected():
    b=bundle();b['images'][0]['crs']=None
    with pytest.raises(InputError,match='georeferenced'):geographic_box(b,[11,12,14,18])


def test_mismatched_grids_rejected():
    b=bundle();b['images'].append(deepcopy(b['images'][0]));b['images'][1]['transform'][2]+=1
    with pytest.raises(InputError,match='same coordinate grid'):geographic_box(b,[11,12,14,18])


def test_crop_updates_geographic_metadata_and_pixels():
    b=bundle();b['images'][0]['array'][0,20:80,10:40]=7
    cropped=crop_bundle(b,{'box':[10,20,40,80]})
    assert cropped['images'][0]['shape']==[60,30]
    assert (cropped['images'][0]['array'][0]==7).all()
    assert cropped['metadata']['geo_bounds']=={'west':11,'south':12,'east':14,'north':18,'center':{'lat':15,'lng':12.5}}


def test_followup_offsets_nested_crop_and_rejects_missing_source():
    import gateway.app as app
    from fastapi import HTTPException
    parent={'status':'complete','_paths':['fixture'],'_options':[{}],'_scenario':'SINGLE',
            'result':{'input':{'images':[{'roi':[10,20,40,80]}]}}}
    with patch.dict(app.jobs, {'area-test':parent}), patch.object(app,'validate',return_value=bundle()), patch.object(app,'start',return_value={'job_id':'new'}) as start:
        asyncio.run(app.followup('area-test',app.Followup(query='Describe this area',box=[1,2,5,6])))
        assert start.call_args.kwargs['roi']=={'box':[11,22,15,26]}
        asyncio.run(app.followup('area-test',app.Followup(query='Describe this area',bounds=[11,12,14,18])))
        assert start.call_args.kwargs['roi']=={'box':[10,20,40,80]}
        with pytest.raises(HTTPException) as invalid:
            asyncio.run(app.followup('area-test',app.Followup(query='Describe this area',bounds=[9,12,14,18])))
        assert invalid.value.status_code==422
        with pytest.raises(HTTPException) as ambiguous:
            asyncio.run(app.followup('area-test',app.Followup(query='Describe this area',bounds=[11,12,14,18],box=[1,2,5,6])))
        assert ambiguous.value.status_code==422
        with pytest.raises(HTTPException) as error:
            asyncio.run(app.followup('area-test',app.Followup(query='Describe this area',box=[1,2,35,6])))
        assert error.value.status_code==422
    with pytest.raises(HTTPException) as error:
        asyncio.run(app.followup('missing',app.Followup(query='Describe this area',box=[1,2,5,6])))
    assert error.value.status_code==409


def test_history_survives_session_restart_and_includes_older_reports(tmp_path):
    import json
    import gateway.app as app
    for i in range(35):
        (tmp_path/f'{i:032x}.json').write_text(json.dumps({'query_id':f'{i:032x}','query':f'Saved {i}','input':{'images':[]}}))
    (tmp_path/'broken.json').write_text('{')
    with patch.object(app,'REPORTS',tmp_path), patch.dict(app.jobs,{},clear=True):
        assert len(app.history())==35
        assert app.report(f'{0:032x}.json').path==tmp_path/f'{0:032x}.json'
