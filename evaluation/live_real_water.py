"""Exercise real TIFF uploads, model routing, previews and downloadable reports."""
import json,time
from pathlib import Path
from contextlib import ExitStack
import requests
ROOT=Path(__file__).resolve().parents[1]

def main():
    base='http://127.0.0.1:8000'
    rows=json.loads((ROOT/'data/sen1floods11/manifest.json').read_text())
    row=next(r for r in rows if r['split']=='test');results=[]
    for kind,keys,opts,scenario in [('optical',['s2'],row['options'][:1],'SINGLE'),('sar',['s1'],row['options'][1:],'SINGLE'),('joint',['s2','s1'],row['options'],'CROSS_MODAL_PAIR')]:
        with ExitStack() as stack:
            files=[('images',(Path(row[k]).name,stack.enter_context((ROOT/row[k]).open('rb')),'image/tiff')) for k in keys]
            response=requests.post(base+'/api/jobs',files=files,data={'scenario':scenario,'options':json.dumps(opts),'query':'What areas are covered by water?'},timeout=60)
        response.raise_for_status();job_id=response.json()['job_id'];deadline=time.monotonic()+180
        while time.monotonic()<deadline:
            r=requests.get(base+'/api/jobs/'+job_id,timeout=30);r.raise_for_status();job=r.json()
            if job['status'] in ('complete','failed'):break
            time.sleep(.5)
        assert job['status']=='complete',job
        out=job['result'];assert out['task']=='WATER_ANALYSIS' and out['specialists'][0]['status']=='complete'
        for link in [out['report_url'],out['html_report_url'],*out['previews']]:
            asset=requests.get(base+link,timeout=30);asset.raise_for_status();assert asset.content
        results.append({'kind':kind,'job_id':job_id,'task':out['task'],'mode':out['specialists'][0]['mode'],
                        'trust':out['trust_score'],'decision':out['decision'],'report':out['report_url'],
                        'preprocessing':[s['code'] for s in out['input']['validation']['preprocessing_steps']]})
        print(kind,job_id,out['trust_score'],flush=True)
    (ROOT/'evaluation/live_real_water_summary.json').write_text(json.dumps(results,indent=2))
if __name__=='__main__':main()
