"""Acceptance against the running gateway, including downloadable reports."""
import argparse,json,time
from pathlib import Path
import requests

def main():
    p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8000');args=p.parse_args()
    root=Path(__file__).resolve().parents[1];results=[]
    for name in ['vqa','grounding','change','fusion']:
        response=requests.post(args.url+'/api/demos/'+name,timeout=30);response.raise_for_status();key=response.json()['job_id']
        deadline=time.monotonic()+180
        while time.monotonic()<deadline:
            response=requests.get(args.url+'/api/jobs/'+key,timeout=15);response.raise_for_status();job=response.json()
            if job['status']!='running':break
            time.sleep(.25)
        assert job['status']=='complete',job
        result=job['result'];report=requests.get(args.url+result['report_url'],timeout=15);report.raise_for_status()
        assert report.json()==result
        assert {'neural','symbolic','coverage'}<=result['confidence_breakdown'].keys()
        assert len(result['execution_trace'])>=10
        for preview in result['previews']:
            response=requests.get(args.url+preview,timeout=15);response.raise_for_status();assert response.headers['content-type']=='image/png'
        if name!='vqa':assert result['overlay'] and result['overlay']['data']
        results.append({'demo':name,'status':'passed','task':result['task'],'trace_events':len(result['execution_trace']),
            'modes':[o['mode'] for o in result['specialists']],'report_download':'passed','preview_download':'passed','trust':result['trust_score']})
        print(name,'passed',flush=True)
    (root/'tests/live_acceptance_results.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
if __name__=='__main__':main()
