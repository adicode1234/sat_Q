"""Exercise production HTTP dispatch through real independent Uvicorn services.
No Docker required. Uses OS-assigned ports and stops only its own child processes.
"""
import json,os,re,subprocess,sys,tempfile,time
from pathlib import Path
import httpx,yaml
from controller.pipeline import run_pipeline
ROOT=Path(__file__).resolve().parents[1]

def main():
    processes=[];handles=[];urls={};results=[]
    original={k:os.environ.get(k) for k in ('SATQUERY_SERVING','SATQUERY_SERVICE_URLS','SATQUERY_USE_VILT')}
    os.environ['SATQUERY_USE_VILT']='0'
    try:
        # Windows may briefly retain log handles after a process exits. Cleanup
        # of disposable logs must not hide successful assertions or process exit.
        with tempfile.TemporaryDirectory(prefix='satquery-http-',ignore_cleanup_errors=True) as directory:
            for tool in yaml.safe_load((ROOT/'configs/tool_registry.yaml').read_text())['tools']:
                path=Path(directory)/(tool['name']+'.log');handle=path.open('w');handles.append(handle)
                environment={**os.environ,'TOOL_MODULE':tool['module'],'PYTHONUNBUFFERED':'1'}
                process=subprocess.Popen([sys.executable,'-m','uvicorn','models.service:app','--host','127.0.0.1','--port','0'],cwd=ROOT,env=environment,stdout=handle,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
                processes.append(process);deadline=time.monotonic()+25
                while time.monotonic()<deadline:
                    log=path.read_text(errors='replace');match=re.search(r'Uvicorn running on http://127\.0\.0\.1:(\d+)',log)
                    if match:
                        base=f'http://127.0.0.1:{match[1]}'
                        response=httpx.get(base+'/health',timeout=5);response.raise_for_status();urls[tool['name']]=base+'/run';break
                    if process.poll() is not None:raise RuntimeError(log)
                    time.sleep(.1)
                else:raise RuntimeError('Service startup timed out: '+tool['name'])
            os.environ['SATQUERY_SERVICE_URLS']=json.dumps(urls)
            for demo in json.loads((ROOT/'data/demo/manifest.json').read_text()):
                args=([ROOT/p for p in demo['paths']],demo['options'],demo['scenario'],demo['query'])
                os.environ['SATQUERY_SERVING']='in_process';local=run_pipeline(*args)
                os.environ['SATQUERY_SERVING']='http';remote=run_pipeline(*args)
                assert remote['answer']==local['answer'],demo['id']
                assert remote['trust_score']==local['trust_score'],demo['id']
                assert remote['overlay']==local['overlay'],demo['id']
                assert any(e['action']=='http_request' for e in remote['execution_trace'])
                results.append({'demo':demo['id'],'status':'passed','http_calls':sum(e['action']=='http_request' for e in remote['execution_trace'])})
            (ROOT/'tests/http_services_results.json').write_text(json.dumps({'transport':'real loopback HTTP','services':len(urls),'results':results,'docker_runtime_verified':False},indent=2))
            print(json.dumps(results,indent=2))
            # Close children before TemporaryDirectory removes their open log files.
            for p in processes:p.terminate()
            for p in processes:p.wait(timeout=10)
            for h in handles:h.close()
    finally:
        for p in processes:
            if p.poll() is None:p.terminate();p.wait(timeout=10)
        for h in handles:h.close()
        for k,v in original.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v
if __name__=='__main__':main()
