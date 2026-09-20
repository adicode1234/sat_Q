import argparse, json, time
from pathlib import Path
import requests

p=argparse.ArgumentParser(); p.add_argument('--root',required=True); args=p.parse_args()
root=Path(args.root); outdir=root/'docs'/'evidence'; outdir.mkdir(parents=True,exist_ok=True)
img=root/'data'/'demo'/'optical_after.tif'
if not img.exists(): img=root/'data'/'demo'/'optical_after.png'
if not img.exists(): raise SystemExit('Demo optical image not found')
base='http://127.0.0.1:8000'
queries=[('water_a','Locate the surface water.'),('water_b','Where is the water body in this image?'),('water_c','Highlight regions containing water.'),('contrast','Locate buildings in this image.')]

def boxes_from(job):
    result=job.get('result') or {}; overlay=result.get('overlay') or {}
    if overlay.get('type')!='bbox': return []
    out=[]
    for d in overlay.get('data') or []:
        b=d.get('box') if isinstance(d,dict) else None
        if b and len(b)==4: out.append([float(x) for x in b])
    return out

def iou(a,b):
    x1=max(a[0],b[0]); y1=max(a[1],b[1]); x2=min(a[2],b[2]); y2=min(a[3],b[3])
    inter=max(0,x2-x1)*max(0,y2-y1); aa=max(0,a[2]-a[0])*max(0,a[3]-a[1]); bb=max(0,b[2]-b[0])*max(0,b[3]-b[1])
    return inter/max(aa+bb-inter,1e-9)

rows=[]
for key,q in queries:
    with img.open('rb') as f:
        files={'images':(img.name,f,'image/tiff' if img.suffix.lower() in {'.tif','.tiff'} else 'image/png')}
        data={'scenario':'SINGLE','query':q,'options':json.dumps([{'modality':'optical','bands':['red','green','blue','nir','swir']}])}
        r=requests.post(base+'/api/jobs',files=files,data=data,timeout=60); r.raise_for_status(); jid=r.json()['job_id']
    job=None
    for _ in range(180):
        time.sleep(2); rr=requests.get(base+f'/api/jobs/{jid}',timeout=30); rr.raise_for_status(); job=rr.json()
        if job.get('status') not in {'queued','validating','running','verifying'}: break
    result=job.get('result') or {}
    dec=result.get('decision')
    rows.append({'key':key,'query':q,'job_id':jid,'status':job.get('status'),'task':result.get('task'),'boxes':boxes_from(job),'answer':result.get('answer'),'decision':dec.get('status') if isinstance(dec,dict) else dec})

waters=[r for r in rows if r['key'].startswith('water_') and r['boxes']]
consistency=[]
for i in range(len(waters)):
    for j in range(i+1,len(waters)): consistency.append(iou(waters[i]['boxes'][0],waters[j]['boxes'][0]))
contrast=next((r for r in rows if r['key']=='contrast'),None)
contrast_iou=iou(waters[0]['boxes'][0],contrast['boxes'][0]) if waters and contrast and contrast['boxes'] else None
proof={'generated_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'image':str(img.relative_to(root)),'rows':rows,'water_paraphrase_mean_iou':sum(consistency)/len(consistency) if consistency else None,'water_vs_buildings_iou':contrast_iou,'all_jobs_complete':all(r['status']=='complete' for r in rows),'interpretation':'Same-concept paraphrases should be spatially consistent when evidence exists; a semantically different query should be allowed to return a different region or no region.'}
(outdir/'GROUNDING_PARAPHRASE_PROOF.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
md=['# Grounding Paraphrase / Contrast Proof','',f"Input: `{proof['image']}`",'', '| Query | Status | Task | Boxes | Decision |','|---|---|---|---:|---|']
for r in rows: md.append(f"| {r['query']} | {r['status']} | {r['task'] or ''} | {len(r['boxes'])} | {r['decision'] or ''} |")
md += ['',f"Mean IoU among water paraphrases: **{proof['water_paraphrase_mean_iou']}**",f"Water-vs-buildings first-box IoU: **{proof['water_vs_buildings_iou']}**",'',proof['interpretation']]
(outdir/'GROUNDING_PARAPHRASE_PROOF.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps(proof,indent=2))
if not proof['all_jobs_complete']: raise SystemExit(2)
