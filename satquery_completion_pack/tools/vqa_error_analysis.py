import argparse, json, collections
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();root=Path(a.root);outdir=root/'docs'/'evidence';outdir.mkdir(parents=True,exist_ok=True)
path=root/'evaluation'/'results.json'; data=json.loads(path.read_text(encoding='utf-8')); rows=data.get('samples') or []

def val(r,*keys):
    for k in keys:
        if r.get(k) not in (None,''): return r.get(k)
    return None
wrong=[]; pairs=collections.Counter(); byds=collections.Counter(); total=collections.Counter()
for r in rows:
    ds=r.get('dataset','UNKNOWN'); total[ds]+=1; em=r.get('exact_match')
    if em in (False,0,0.0,None):
        exp=val(r,'expected','reference','ground_truth','label'); pred=val(r,'prediction','answer','short_answer')
        wrong.append({'dataset':ds,'id':r.get('id'),'query':val(r,'query','question'),'expected':exp,'predicted':pred,'model_modes':r.get('model_modes'),'decision':r.get('decision')}); byds[ds]+=1; pairs[(str(exp),str(pred))]+=1
summary={'total_samples':len(rows),'wrong_or_nonexact':len(wrong),'wrong_by_dataset':dict(byds),'total_by_dataset':dict(total),'top_expected_predicted_pairs':[{'expected':k[0],'predicted':k[1],'count':v} for k,v in pairs.most_common(20)],'wrong':wrong}
(outdir/'VQA_ERROR_ANALYSIS.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
md=['# VQA Error Analysis','',f"Samples in promoted evaluation: **{len(rows)}**",f"Wrong/non-exact rows: **{len(wrong)}**",'', '## By dataset','']
for ds,n in total.items(): md.append(f'- {ds}: {byds[ds]} wrong/non-exact out of {n}')
md += ['','## Most common expected → predicted pairs','']
for x in summary['top_expected_predicted_pairs']: md.append(f"- `{x['expected']}` → `{x['predicted']}`: {x['count']}")
md += ['','## Priority','', 'Focus model work on repeated systematic answer confusions. Do not tune against held-out evaluation labels directly; use separate training/validation data.']
(outdir/'VQA_ERROR_ANALYSIS.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='wrong'},indent=2))
