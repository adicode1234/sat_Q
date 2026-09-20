import argparse, json, time
from pathlib import Path
import requests

p=argparse.ArgumentParser(); p.add_argument('--root',required=True); args=p.parse_args()
root=Path(args.root); outdir=root/'docs'/'evidence'; outdir.mkdir(parents=True,exist_ok=True)
base='http://127.0.0.1:8000'

def get_json(url):
    r=requests.get(url,timeout=30); r.raise_for_status(); return r.json()

demos=get_json(base+'/api/demos')
if isinstance(demos,dict): demos=demos.get('demos') or demos.get('items') or []
if not isinstance(demos,list) or not demos: raise SystemExit('No demos returned by /api/demos')
rows=[]
for demo in demos:
    did=demo.get('id'); title=demo.get('title',did)
    r=requests.post(f'{base}/api/demos/{did}',timeout=30); r.raise_for_status(); job_id=r.json()['job_id']
    job=None
    for _ in range(180):
        time.sleep(2); job=get_json(f'{base}/api/jobs/{job_id}')
        if job.get('status') not in {'queued','validating','running','verifying'}: break
    result=job.get('result') or {}
    specs=result.get('specialists') or []
    modes=[]
    for s in specs:
        modes.append((s.get('mode') or s.get('name') or '?') if isinstance(s,dict) else str(s))
    decision=result.get('decision') or {}
    rows.append({'demo':did,'title':title,'job_id':job_id,'status':job.get('status'),'task':result.get('task'),'specialists':modes,'trust_score':result.get('trust_score'),'decision':decision.get('status') if isinstance(decision,dict) else decision,'events':len(job.get('events') or result.get('execution_trace') or []),'error':job.get('error')})

payload={'generated_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'rows':rows,'all_complete':all(r['status']=='complete' for r in rows)}
(outdir/'FINAL_E2E_PROOF.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
md=['# SatQuery Final Post-Rebuild E2E Proof','',f"All demos complete: **{payload['all_complete']}**",'', '| Demo | Status | Task | Specialists | Decision | Trust | Events |','|---|---|---|---|---|---:|---:|']
for r in rows:
    md.append(f"| {r['demo']} | {r['status']} | {r['task'] or ''} | {', '.join(r['specialists'])} | {r['decision'] or ''} | {r['trust_score'] if r['trust_score'] is not None else ''} | {r['events']} |")
md += ['', 'A LOW_TRUST / INSUFFICIENT_EVIDENCE decision can be scientifically correct; pipeline success is represented by terminal job status `complete`.']
(outdir/'FINAL_E2E_PROOF.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps(payload,indent=2))
if not payload['all_complete']: raise SystemExit(2)
