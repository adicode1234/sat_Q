"""Batch evaluation goes through exactly the production controller and verification."""
import json,re,time,argparse,hashlib
from datetime import datetime,timezone
from collections import Counter
from pathlib import Path
from controller.pipeline import run_pipeline
ROOT=Path(__file__).resolve().parents[1]

def normalize(s):return ' '.join(re.findall(r'\w+',str(s).lower()))
def token_f1(pred,ref):
    a=Counter(normalize(pred).split());b=Counter(normalize(ref).split());n=sum((a&b).values())
    return 2*n/max(sum(a.values())+sum(b.values()),1)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--manifest',default='evaluation/samples.json');parser.add_argument('--limit',type=int,default=0);parser.add_argument('--output',default='evaluation/results.json');args=parser.parse_args()
    path=ROOT/args.manifest;samples=json.loads(path.read_text()) if path.exists() else [];rows=[]
    if not samples:raise ValueError('No evaluation samples; no scores can be computed')
    if args.limit:
        samples=[s for name in ('VRSBench','RSVQA','CDVQA') for s in [s for s in samples if s['dataset']==name][:args.limit]]
    train_hashes=set()
    training=ROOT/'data/vrsbench/train.jsonl'
    if training.exists():
        for line in training.read_text().splitlines():
            if line.strip():train_hashes.add(hashlib.sha256((ROOT/json.loads(line)['image']).read_bytes()).hexdigest())
    training=ROOT/'data/cdvqa/train/manifest.json'
    if training.exists():
        for row in json.loads(training.read_text()):
            for p in row['paths']:train_hashes.add(hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
    for sample in samples:
        mirror_test=sample['split']=='test_mirror' and sample.get('source_metadata',{}).get('split')=='test'
        if not mirror_test and sample['split'] not in ('official_eval','official_test','test','validation','val'):raise ValueError('Evaluation requires an explicit held-out split')
        hashes=[hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sample['paths']]
        if any(h in train_hashes for h in hashes):raise ValueError('Train/evaluation image content overlap')
        if sample.get('sha256') and hashes!=sample['sha256']:raise ValueError('Evaluation input hash mismatch')
    for sample in samples:
        started=time.perf_counter()
        try:
            out=run_pipeline([ROOT/p for p in sample['paths']],sample['options'],sample['scenario'],sample['query'])
            # Score the production short-answer field when available. This field
            # is created without access to references and is included in reports.
            pred=out.get('short_answer') or out['answer'];ref=sample['answer']
            rows.append({'dataset':sample['dataset'],'split':sample['split'],'id':sample['id'],'task':out['task'],
                         'reference':ref,'prediction':pred,'full_answer':out['answer'],'exact_match':float(normalize(pred)==normalize(ref)),
                         'token_f1':token_f1(pred,ref),'trust':out['trust_score'],'elapsed_s':time.perf_counter()-started,
                         'model_modes':[s['mode'] for s in out['specialists']], 'evidence_coverage':out['confidence_breakdown']['coverage'],
                         'decision':out.get('decision'),'provenance':out.get('provenance'),
                         'trace':out['execution_trace'],'status':'complete'})
        except Exception as exc:rows.append({'dataset':sample['dataset'],'split':sample['split'],'id':sample['id'],'status':'failed','error':str(exc)})
    datasets={}
    for name in ['VRSBench','RSVQA','CDVQA']:
        selected=[r for r in rows if r['dataset']==name];ok=[r for r in selected if r['status']=='complete']
        datasets[name]={'requested':len(selected),'completed':len(ok),'failed':len(selected)-len(ok),
                        'splits':sorted(set(r['split'] for r in selected)),
                        'exact_match':sum(r['exact_match'] for r in ok)/len(selected) if selected else None,
                        'token_f1':sum(r['token_f1'] for r in ok)/len(selected) if selected else None}
    valid=[d['exact_match'] for d in datasets.values() if d['exact_match'] is not None]
    by_task={}
    for task in sorted({r['task'] for r in rows if r['status']=='complete'}):
        selected=[r for r in rows if r.get('task')==task]
        by_task[task]={'completed':len(selected),'exact_match':sum(r['exact_match'] for r in selected)/len(selected),'token_f1':sum(r['token_f1'] for r in selected)/len(selected)}
    result={'status':'PARTIAL','evaluation_date':datetime.now(timezone.utc).isoformat(),'manifest_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'scope':'SMALL PUBLIC-DATA SMOKE EVALUATION; not full benchmark reproduction',
            'datasets':datasets,'tasks':by_task,'combined_exact_match':sum(valid)/len(valid) if valid else None,
            'normalization':'Macro average of available dataset exact-match scores (0–1); failed requests count as zero. Missing datasets are excluded and separately disclosed.',
            'official_test_suite_complete':False,
            'limitations':['This is a bounded test-split sample, not a complete leaderboard reproduction.','VRSBench and CDVQA slices are small; RSVQA uses round-robin selection across official test images.','The production short_answer field is scored when present; otherwise the full evidence answer is scored. These are not leaderboard-equivalent caption metrics.','Synthetic training accuracy is never included in benchmark scores.'],
            'samples':rows}
    destination=ROOT/args.output
    if destination.exists():
        history=ROOT/'evaluation/runs';history.mkdir(exist_ok=True)
        (history/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-previous.json')).write_bytes(destination.read_bytes())
    destination.write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='samples'},indent=2))
if __name__=='__main__':main()
