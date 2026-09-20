import argparse, json, time, traceback
from pathlib import Path
import numpy as np, requests, rasterio
from rasterio.transform import Affine
p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();root=Path(a.root);outdir=root/'docs'/'evidence';outdir.mkdir(parents=True,exist_ok=True);proxy=root/'data'/'real_proxy';proxy.mkdir(parents=True,exist_ok=True);report=root/'docs'/'REAL_WORLD_PROXY_TEST.md'
try:
    from datasets import load_dataset
    ds=load_dataset('Hermanni/sen12mscr',split='train',streaming=True)
    row=next(iter(ds))
    s1=np.frombuffer(row['sar'],dtype=np.float32).reshape(row['sar_shape'])
    s2=np.frombuffer(row['target'],dtype=np.int16).reshape(row['opt_shape'])
    if s2.ndim==3 and s2.shape[-1] in (12,13): s2=np.moveaxis(s2,-1,0)
    if s1.ndim==3 and s1.shape[0] not in (1,2) and s1.shape[-1] in (1,2): s1=np.moveaxis(s1,-1,0)
    s2p=proxy/'sen12mscr_s2_real_sensor_proxy.tif'; s1p=proxy/'sen12mscr_s1_real_sensor_proxy.tif'; transform=Affine.identity(); s2bands=['B01','B02','B03','B04','B05','B06','B07','B08','B8A','B09','B10','B11','B12'][:s2.shape[0]]
    with rasterio.open(s2p,'w',driver='GTiff',height=s2.shape[1],width=s2.shape[2],count=s2.shape[0],dtype=s2.dtype,transform=transform) as dst:
        dst.write(s2)
        for i,b in enumerate(s2bands,1): dst.set_band_description(i,b)
        dst.update_tags(source_dataset='SEN12MS-CR',sensor='Sentinel-2',source_mirror='Hugging Face Hermanni/sen12mscr',original_source='mediaTUM 1554803',coregistered_pair='true',georeference_note='Original CRS/geotransform not preserved in this mirror conversion')
    with rasterio.open(s1p,'w',driver='GTiff',height=s1.shape[1],width=s1.shape[2],count=s1.shape[0],dtype=s1.dtype,transform=transform) as dst:
        dst.write(s1)
        for i,b in enumerate(['VV','VH'][:s1.shape[0]],1): dst.set_band_description(i,b)
        dst.update_tags(source_dataset='SEN12MS-CR',sensor='Sentinel-1',source_mirror='Hugging Face Hermanni/sen12mscr',original_source='mediaTUM 1554803',coregistered_pair='true',sar_units='dB',georeference_note='Original CRS/geotransform not preserved in this mirror conversion')
    provenance={'dataset':'SEN12MS-CR','mirror':'Hermanni/sen12mscr','original_source':'mediaTUM 1554803','season':row.get('season'),'scene':row.get('scene'),'patch':row.get('patch'),'s1_shape':list(s1.shape),'s2_shape':list(s2.shape),'note':'Real Sentinel-1/Sentinel-2 paired sample. Mirror row does not expose original CRS/geotransform.'}
    (proxy/'PROVENANCE.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    base='http://127.0.0.1:8000'; options=[{'modality':'optical','bands':s2bands,'benchmark_source':'SEN12MS-CR real Sentinel-2 proxy via Hugging Face; original mediaTUM 1554803','coregistered':True},{'modality':'SAR','bands':['VV','VH'][:s1.shape[0]],'sar_units':'db','benchmark_source':'SEN12MS-CR real Sentinel-1 proxy via Hugging Face; original mediaTUM 1554803','coregistered':True}]
    with s2p.open('rb') as fo, s1p.open('rb') as fs:
        files=[('images',(s2p.name,fo,'image/tiff')),('images',(s1p.name,fs,'image/tiff'))]; data={'scenario':'CROSS_MODAL_PAIR','query':'Compare the optical and SAR observations and report only evidence supported across the real Sentinel-1/Sentinel-2 pair.','options':json.dumps(options)}; r=requests.post(base+'/api/jobs',files=files,data=data,timeout=120); r.raise_for_status(); jid=r.json()['job_id']
    job=None
    for _ in range(240):
        time.sleep(2); rr=requests.get(base+f'/api/jobs/{jid}',timeout=30); rr.raise_for_status(); job=rr.json()
        if job.get('status') not in {'queued','validating','running','verifying'}: break
    (outdir/'REAL_PROXY_JOB.json').write_text(json.dumps({'provenance':provenance,'job':job},indent=2),encoding='utf-8')
    result=(job or {}).get('result') or {}; dec=result.get('decision') or {}; validation=result.get('validation') or result.get('input_validation')
    md=f'''# Real-World Optical/SAR Proxy Test

Status: **{(job or {}).get('status')}**

## Provenance

- Dataset: SEN12MS-CR
- Real sensors: Sentinel-1 SAR + Sentinel-2 multispectral
- Mirror used for one streamed sample: Hugging Face `Hermanni/sen12mscr`
- Original source declared by the mirror: mediaTUM 1554803
- Season: `{row.get('season')}`
- Scene: `{row.get('scene')}`
- Patch: `{row.get('patch')}`
- S1 shape: `{list(s1.shape)}`
- S2 shape: `{list(s2.shape)}`

## SatQuery result

- Job ID: `{jid}`
- Task: `{result.get('task')}`
- Decision: `{dec.get('status') if isinstance(dec,dict) else dec}`
- Trust score: `{result.get('trust_score')}`
- Validation: `{json.dumps(validation,ensure_ascii=False) if validation is not None else 'see REAL_PROXY_JOB.json'}`

## Scientific boundary

This is a **real-sensor Sentinel-1/Sentinel-2 cross-modal proxy run**. The mirror provides paired sensor arrays but does not expose the original product CRS/geotransform in each row. The generated local TIFFs intentionally do **not** invent a CRS. Any SatQuery `READY_WITH_LIMITATIONS` / metadata warning is expected and should be preserved in the evidence.

This test does **not** prove Cartosat-2S/RISAT performance and must not be presented as such.
'''
    report.write_text(md,encoding='utf-8'); print(json.dumps({'job_id':jid,'status':(job or {}).get('status'),'provenance':provenance},indent=2))
    if (job or {}).get('status')!='complete': raise SystemExit(2)
except Exception:
    err=traceback.format_exc(); report.write_text(f'''# Real-World Optical/SAR Proxy Test

Status: **PARTIAL / ATTEMPT FAILED**

A real SEN12MS-CR Sentinel-1/Sentinel-2 proxy run was attempted, but it did not complete.

```text
{err}
```

Do not claim real proxy validation until this test reaches a terminal SatQuery status of `complete`.
''',encoding='utf-8'); print(err); raise SystemExit(2)
