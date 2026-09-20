"""Explicit local Docker acceptance run; never evaluates or writes benchmark scores."""
import hashlib
import json
import runpy
import sys
import time
from pathlib import Path
import requests
import numpy as np
from rasterio.transform import from_bounds

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
BASE='http://127.0.0.1:8080'
OUT=ROOT/'docs/evidence/input-normalization'
OUT.mkdir(parents=True,exist_ok=True)
FIXTURES=ROOT/'.test-runs/normalization-live-fixtures'
FIXTURES.mkdir(parents=True,exist_ok=True)
tif=runpy.run_path(str(ROOT/'tests/test_normalization.py'))['tif']
proof={'fixture_note':'Generated acceptance rasters reproduce the specified river dimensions; these are not the user original river files.'}


def wait_job(key):
    deadline=time.monotonic()+300
    while time.monotonic()<deadline:
        response=requests.get(BASE+'/api/jobs/'+key,timeout=20);response.raise_for_status();job=response.json()
        if job['status']=='failed':raise AssertionError(job)
        if job['status']=='complete':return job['result']
        time.sleep(.5)
    raise AssertionError('Job deadline exceeded')


def submit(paths,options,scenario,query,endpoint='/api/jobs'):
    handles=[p.open('rb') for p in paths]
    try:
        response=requests.post(BASE+endpoint,files=[('images',(p.name,f)) for p,f in zip(paths,handles)],
                               data={'options':json.dumps(options),'scenario':scenario,'query':query},timeout=120)
        response.raise_for_status()
        return response.json()
    finally:
        for f in handles:f.close()


proof['health']=requests.get(BASE+'/api/health',timeout=30).json()
assert proof['health']['all_specialists_ready']
proof['config']=requests.get(BASE+'/api/config',timeout=20).json()
assert proof['config']['max_multidate']==20
benchmark_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'evaluation').glob('*.json')}
benchmark=requests.get(BASE+'/api/benchmarks',timeout=30);benchmark.raise_for_status()
proof['benchmark_api_status']=benchmark.status_code
assert requests.get(BASE+'/api/registry',timeout=20).status_code==200

before=tif(FIXTURES/'river_before_fixture.tif',(710,1600),crs='EPSG:4326',transform=from_bounds(77,12,77.16,12.071,1600,710))
after=tif(FIXTURES/'river_after_fixture.tif',(709,1600),crs='EPSG:4326',transform=from_bounds(77,12,77.16,12.071,1600,709))
options=[{'date':'2024-01-01'},{'date':'2024-02-01'}]
inspection=submit([before,after],options,'BITEMPORAL_PAIR','Where is the change mask?','/api/inspect')
assert inspection['validation_status']=='READY_WITH_PREPROCESSING'
assert [i['shape'] for i in inspection['images']]==[[710,1600],[710,1600]]
proof['river_inspection']=inspection
(OUT/'river-inspection.json').write_text(json.dumps(inspection,indent=2),encoding='utf-8')
result=wait_job(submit([before,after],options,'BITEMPORAL_PAIR','Where is the change mask?')['job_id'])
assert result['task']=='CHANGE_MASK'
assert all(s['status']=='complete' for s in result['specialists']),result['specialists']
assert any(e['action']=='automatic_preprocessing' for e in result['execution_trace'])
assert all(i['bands']==['red','green','blue'] for i in result['input']['images'])
for url in result['previews']+[result['html_report_url'],result['report_url']]:
    assert requests.get(BASE+url,timeout=20).status_code==200
proof['river_job']={'job_id':result['query_id'],'status':result['input']['validation_status'],
                    'decision':result['decision'],'specialists':[(s['model'],s['status']) for s in result['specialists']]}

followup=requests.post(BASE+f'/api/jobs/{result["query_id"]}/followup',json={'query':'Where is the change mask?','box':[10,10,100,100]},timeout=60)
followup.raise_for_status();roi=wait_job(followup.json()['job_id'])
assert all(i['shape']==[90,90] for i in roi['input']['images'])
assert all(s['status']=='complete' for s in roi['specialists'])
proof['roi_followup']={'job_id':roi['query_id'],'shape':[90,90]}

from PIL import Image
photo=FIXTURES/'visual_fixture.png'
Image.fromarray(np.random.default_rng(3).integers(0,255,(64,64,3),dtype='uint8')).save(photo)
visual=wait_job(submit([photo],[{}],'SINGLE','Describe the scene')['job_id'])
assert visual['input']['images'][0]['visual_only']
assert not visual['input']['validation']['capabilities']['physical_area']
proof['ordinary_png']={'job_id':visual['query_id'],'status':visual['input']['validation_status']}

proof['demos']={}
for demo in requests.get(BASE+'/api/demos',timeout=20).json():
    started=requests.post(BASE+'/api/demos/'+demo['id'],timeout=20);started.raise_for_status()
    demo_result=wait_job(started.json()['job_id'])
    assert all(s['status']=='complete' for s in demo_result['specialists'])
    proof['demos'][demo['id']]={'job_id':demo_result['query_id'],'task':demo_result['task'],'decision':demo_result['decision']['status']}
    print('Demo passed:',demo['id'],flush=True)

assert requests.get(BASE+'/api/history',timeout=20).status_code==200
assert benchmark_hashes=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'evaluation').glob('*.json')}
proof['benchmark_artifact_hashes_unchanged']=True
proof['status']='PASS'
(OUT/'live-results.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in proof.items() if k!='river_inspection'},indent=2))
