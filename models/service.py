"""Each service hosts a single independently replaceable specialist."""
import os,importlib,threading,time
from pathlib import Path
from fastapi import FastAPI,HTTPException
from gateway.validation import read_image
app=FastAPI(title='SatQuery specialist')
ROOT=Path(__file__).resolve().parents[1]
_run_lock=threading.Lock()
_last_mode=None
@app.get('/health')
def health():
    module=importlib.import_module(os.environ.get('TOOL_MODULE','models.vqa_caption.model'))
    return {'status':'ok','module':module.__name__,'last_executed_mode':_last_mode,
            'model_loaded':bool(getattr(module,'_model',None) is not None or getattr(module,'_vilt',None) is not None),
            'busy':_run_lock.locked()}
@app.post('/run')
def run(payload:dict):
    global _last_mode
    try:
        bundle=payload['bundle'];images=[]
        for image in bundle['images']:
            path=Path(image['path']).resolve()
            if not path.is_relative_to(ROOT/'data'):raise ValueError('Only shared data paths are accepted')
            loaded=read_image(path,image['id'],image)
            loaded.update({k:v for k,v in image.items() if k not in ('array','path','shape','transform','raster_metadata')})
            images.append(loaded)
        hydrated={**bundle,'images':images}
        if bundle.get('roi'):
            from gateway.regions import crop_bundle
            hydrated=crop_bundle(hydrated,bundle['roi'])
        from gateway.contracts import checked_output
        with _run_lock:
            started=time.perf_counter()
            module=os.environ['TOOL_MODULE'];raw=importlib.import_module(module).run(hydrated,payload['call'])
            _last_mode=raw['mode']
            return checked_output(raw,{'name':module,'version':'1'},payload['call'],time.perf_counter()-started)
    except (ValueError,KeyError) as exc:raise HTTPException(422,str(exc)) from exc
