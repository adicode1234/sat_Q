import asyncio,json,uuid,os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, Query, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from PIL import Image
from controller.pipeline import run_pipeline
from gateway.validation import read_image,rgb
from gateway.reporting import render_html
import base64
from datetime import datetime, timezone
from gateway.validation import validate,public_contract
from gateway.errors import InputError
from gateway import settings
from pydantic import field_validator
from pydantic import BaseModel,ConfigDict,Field,ValidationError
from typing import Literal
import logging,httpx,yaml,time

ROOT=Path(__file__).resolve().parents[1]

# --- Load .env file (no extra package needed) ---
_env_file = ROOT / '.env'
if _env_file.exists():
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _, _v = _line.partition('=')
                _k = _k.strip()
                _v = _v.strip().strip('"').strip("'")
                if _k and _k not in os.environ:  # don't override existing env vars
                    os.environ[_k] = _v
    print(f"[SatQuery] Loaded environment from {_env_file}", flush=True)
if (ROOT/'models/checkpoints/vilt/pytorch_model.bin').exists() and 'SATQUERY_USE_VILT' not in os.environ:
    os.environ['SATQUERY_USE_VILT'] = '1'
DATA=ROOT/'data/uploads';DATA.mkdir(parents=True,exist_ok=True)
REPORTS=ROOT/'reports';REPORTS.mkdir(exist_ok=True)
app=FastAPI(title='SatQuery AI',version='1.0.0')
from gateway.auth import router as auth_router, protect_workspace, authenticate, check_origin
app.include_router(auth_router)
app.middleware('http')(protect_workspace)
from gateway.cloud_setup import router as cloud_router
app.include_router(cloud_router)

# --- Auto-configure cloud vision from .env after imports ---
# cloud_vision module-level vars are set at import time (before .env loads),
# so we explicitly re-apply env config here.
from models import cloud_vision as _cv
if os.environ.get('SATQUERY_CLOUD_VISION') == '1':
    _cv_provider = os.environ.get('SATQUERY_VISION_PROVIDER', 'gemini')
    if _cv_provider in _cv.PROVIDERS:
        _env_key_name = _cv.PROVIDERS[_cv_provider][2]
        _cv_key = os.environ.get(_env_key_name, '')
        _cv_model = os.environ.get('OPENROUTER_MODEL' if _cv_provider == 'openrouter' else
                                   'GEMINI_MODEL' if _cv_provider == 'gemini' else
                                   'OLLAMA_MODEL' if _cv_provider == 'ollama' else
                                   'NOVITA_MODEL', '')
        _fmt = 'prompt_json' if ':free' in (_cv_model or '') else 'json_schema'
        _cv.configure(_cv_key, True, _cv_provider, model=_cv_model or None, output_format=_fmt)
        print(f"[SatQuery] Cloud Vision auto-enabled: provider={_cv_provider} model={_cv_model or '(default)'} format={_fmt}", flush=True)
jobs={};tasks=set();MAX_BYTES=settings.MAX_BYTES
CAPACITY=asyncio.Semaphore(1)
ACTIVE={'queued','validating','running','verifying'}


class ImageOptions(BaseModel):
    model_config=ConfigDict(extra='forbid')
    modality:Literal['optical','SAR']='optical'
    bands:list[str]|None=None
    date:str|None=None
    sar_units:Literal['unknown','db','linear']='unknown'
    sensor:str|None=Field(default=None,max_length=120)
    reflectance_scale:float|None=Field(default=None,gt=0,allow_inf_nan=False)
    reflectance_offset:float=Field(default=0,allow_inf_nan=False)
    benchmark_source:str|None=Field(default=None,max_length=1000)
    coregistered:bool=False
    time_index:int|None=None


class Followup(BaseModel):
    model_config=ConfigDict(extra='forbid')
    query:str

    @field_validator("query")
    @classmethod
    def normalize_query(cls,value):return settings.query_text(value)
    box:list[int]|None=Field(default=None,min_length=4,max_length=4)
    bounds:list[float]|None=Field(default=None,min_length=4,max_length=4)


def public_job(job):return {k:v for k,v in job.items() if not k.startswith('_')}


def check_request(query,scenario,count):
    try:
        settings.query_text(query)
        settings.check_count(scenario,count)
    except InputError as exc:
        raise HTTPException(422,exc.as_dict()) from exc


def remove_uploads(paths):
    for path in paths:
        path=Path(path).resolve()
        if path.is_relative_to(DATA.resolve()) and path.suffix in ('.tif','.tiff','.png','.jpg','.jpeg'):
            path.unlink(missing_ok=True)

def remove_normalized(job_id):
    # Only gateway-generated hexadecimal job directories, never caller paths.
    if len(job_id)!=32 or any(c not in '0123456789abcdef' for c in job_id):return
    directory=DATA/job_id/'normalized'
    if directory.exists():
        for path in directory.glob('img*.tif'):path.unlink(missing_ok=True)
        if not any(directory.iterdir()):directory.rmdir()
        if not any(directory.parent.iterdir()):directory.parent.rmdir()


@app.get('/api/config')
def configuration():
    return {'max_uploads':settings.MAX_UPLOADS,'max_upload_mb':settings.MAX_UPLOAD_MB,
            'max_query_chars':settings.MAX_QUERY_CHARS,'max_multidate':settings.MAX_MULTIDATE}


@app.get('/api/health')
def health():
    if os.environ.get('SATQUERY_PIPELINE', 'specialists') != 'legacy':
        from models.specialist_runtime import runtime_status
        return {'status': 'ok', 'pipeline': 'specialists', 'specialists': [runtime_status(n) for n in ('GeoChat', 'TEOChat', 'EarthMind')], 'all_specialists_ready': False}
    registry=yaml.safe_load((ROOT/'configs/tool_registry.yaml').read_text())['tools'];services=[]
    for tool in registry:
        if tool.get('pipeline') == 'specialists':continue
        state={'name':tool['name'],'status':'available_in_process','model_loaded':None}
        if os.environ.get('SATQUERY_SERVING')=='http' and tool.get('service'):
            endpoint=json.loads(os.environ.get('SATQUERY_SERVICE_URLS','{}')).get(tool['name'],tool['service'])
            try:
                response=httpx.get(endpoint.rsplit('/',1)[0]+'/health',timeout=2);response.raise_for_status();state.update(response.json())
            except (httpx.HTTPError,ValueError):state['status']='unavailable'
        services.append(state)
    return {'status':'ok','specialists':services,'all_specialists_ready':all(s['status']!='unavailable' for s in services),
            'serving':os.environ.get('SATQUERY_SERVING','in_process'),
            'adapter_ready':(ROOT/'models/checkpoints/rgb_adapter.npz').exists(),
            'vilt_enabled':os.environ.get('SATQUERY_USE_VILT', '1' if (ROOT/'models/checkpoints/vilt/pytorch_model.bin').exists() else '0')=='1',
            'checkpoints':{name:(ROOT/'models/checkpoints'/path).exists() for name,path in {
                'vilt_lora':'vilt_lora/adapter_config.json','grounding_dino':'grounding_dino/model.safetensors',
                'change_siamese':'change_siamese/weights.pt','fusion_cross_attention':'fusion_cross_attention/weights.pt',
                'real_rgb_water':'rgb_water_real.npz','rgb_segformer':'rgb_water_segformer/model.safetensors',
                'real_water_optical':'water_real/optical.npz','real_water_sar':'water_real/sar.npz','real_water_joint':'water_real/joint.npz'}.items()}}

async def uploads(files,options):
    if not 1<=len(files)<=settings.MAX_UPLOADS:
        raise HTTPException(422,InputError(f'Maximum {settings.MAX_UPLOADS} images; received {len(files)}.', 'UPLOAD_COUNT_EXCEEDED').as_dict())
    try:options=json.loads(options)
    except json.JSONDecodeError:raise HTTPException(422,'Invalid image options JSON')
    if not isinstance(options,list) or len(options)!=len(files) or any(not isinstance(o,dict) for o in options):
        raise HTTPException(422,'One options object is required for each image')
    try:options=[ImageOptions.model_validate(o).model_dump(exclude_none=True) for o in options]
    except ValidationError as exc:raise HTTPException(422,'Unsupported or invalid image option') from exc
    paths=[]
    try:
        for f,opts in zip(files,options):
            suffix=Path(f.filename or '').suffix.lower()
            if suffix not in {'.tif','.tiff','.png','.jpg','.jpeg'}:raise HTTPException(422,'Unsupported format')
            content=await f.read(MAX_BYTES+1)
            try:settings.check_size(len(content))
            except InputError as exc:raise HTTPException(413,exc.as_dict()) from exc
            path=DATA/(uuid.uuid4().hex+suffix);path.write_bytes(content);paths.append(path)
            opts['original_filename']=Path((f.filename or '').replace('\\','/')).name
    except Exception:
        remove_uploads(paths);raise
    return paths,options

async def execute(job_id,paths,options,scenario,query,params=None,roi=None,parent_id=None):
    job=jobs[job_id];loop=asyncio.get_running_loop()
    def apply_event(item):
        job['events'].append(item)
        job['status']='validating' if item['action']=='validate_inputs' else 'verifying' if item['action'] in ('symbolic_verification','verification_complete','consensus') else 'running'
    def emit(item):loop.call_soon_threadsafe(apply_event,item)
    try:
        async with CAPACITY:
            result=await asyncio.to_thread(run_pipeline,paths,options,scenario,query,params,emit,analysis_id=job_id,roi=roi,parent_id=parent_id)
        # Drain callbacks emitted by the worker before setting the terminal state.
        await asyncio.sleep(0)
        report_started=time.perf_counter()
        result['query_id']=job_id;result['query']=settings.query_text(query);result['report_url']=f'/reports/{job_id}.json'
        for n,(path,opts) in enumerate(zip(paths,options)):
            normalized=DATA/job_id/'normalized'/f'img{n+1}.tif'
            preview_opts={**opts,'bands':result['input']['images'][n]['bands']}
            if normalized.exists():
                preview_opts.pop('reflectance_scale',None);preview_opts.pop('reflectance_offset',None)
            image=read_image(normalized if normalized.exists() else path,f'img{n+1}',preview_opts)
            image['radiometry']=result['input']['images'][n].get('radiometry',image['radiometry'])
            if roi:
                from gateway.regions import crop_bundle
                image=crop_bundle({'images':[image],'validation':{}},roi)['images'][0]
            Image.fromarray(rgb(image)).save(DATA/f'{job_id}_{n}.png')
        result['previews']=[f'/api/preview/{job_id}/{i}' for i in range(len(paths))]
        result['timestamp']=datetime.now(timezone.utc).isoformat()
        result['html_report_url']=f'/reports/{job_id}.html'
        features=[f for p in result.get('spatial_products',[]) for f in p['geojson']['features']]
        if any(p['geojson']['status']=='READY' for p in result.get('spatial_products',[])):
            result['geojson_url']=f'/reports/{job_id}.geojson'
            (REPORTS/f'{job_id}.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features,'analysis_id':job_id},allow_nan=False),encoding='utf-8')
        embedded=['data:image/png;base64,'+base64.b64encode((DATA/f'{job_id}_{i}.png').read_bytes()).decode('ascii') for i in range(len(paths))]
        (REPORTS/f'{job_id}.html').write_text(render_html({**result,'embedded_previews':embedded}),encoding='utf-8')
        result['timings']['report_generation_s']=time.perf_counter()-report_started
        (REPORTS/f'{job_id}.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
        job.update(status='complete',result=result)
    except Exception as exc:
        logging.exception('Analysis %s failed',job_id)
        error=str(exc) if isinstance(exc,ValueError) else 'Analysis failed; see the structured failure details.'
        failure=exc.as_dict() if isinstance(exc,InputError) else {'status':'INCOMPATIBLE','code':'INVALID_INPUT' if isinstance(exc,ValueError) else 'INTERNAL_ERROR','message':str(exc)}
        job['events'].append({'step':len(job['events'])+1,'action':'error','at':datetime.now(timezone.utc).isoformat(),'status':'failed','analysis_id':job_id,'result':failure})
        job.update(status='failed',error=error,failure=failure)
        if not parent_id:remove_uploads(paths)
        remove_normalized(job_id)

def start(paths,options,scenario,query,params=None,roi=None,parent_id=None):
    query=settings.query_text(query)
    check_request(query,scenario,len(paths))
    if len(jobs)>200:
        for old in list(jobs):
            if jobs[old]['status'] not in ACTIVE:jobs.pop(old);break
    if sum(j['status'] in ACTIVE for j in jobs.values())>=8:raise HTTPException(429,'Analysis queue is full; retry shortly')
    key=uuid.uuid4().hex;jobs[key]={'status':'queued','events':[],'_paths':paths,'_options':options,'_scenario':scenario,'_query':query,'created_at':datetime.now(timezone.utc).isoformat()}
    task=asyncio.create_task(execute(key,paths,options,scenario,query,params,roi,parent_id));tasks.add(task);task.add_done_callback(tasks.discard)
    return {'job_id':key}

@app.post('/api/jobs')
async def create_job(images:list[UploadFile]=File(...),query:str=Form(...),scenario:str=Form('SINGLE'),options:str=Form('[{"modality":"optical"}]')):
    check_request(query,scenario,len(images))
    paths,opts=await uploads(images,options)
    try:return start(paths,opts,scenario,query)
    except Exception:remove_uploads(paths);raise

@app.post('/api/analyze')
async def analyze(images:list[UploadFile]=File(...),query:str=Form(...),scenario:str=Form('SINGLE'),options:str=Form('[{"modality":"optical"}]')):
    check_request(query,scenario,len(images))
    paths,opts=await uploads(images,options)
    if sum(j['status'] in ACTIVE for j in jobs.values())>=8:
        remove_uploads(paths);raise HTTPException(429,'Analysis queue is full')
    job_id=uuid.uuid4().hex;jobs[job_id]={'status':'queued','events':[]}
    await execute(job_id,paths,opts,scenario,query)
    if jobs[job_id]['status']=='failed':raise HTTPException(422,{'error':jobs[job_id]['error'],'failure':jobs[job_id]['failure'],'execution_trace':jobs[job_id]['events']})
    return jobs[job_id]['result']

@app.post('/api/translate')
async def api_translate(req: Request):
    from gateway.translator import translate_texts
    try:
        data = await req.json()
        texts = data.get('texts', [])
        target = data.get('target', 'hi')
        if isinstance(texts, str):
            texts = [texts]
        translated = await asyncio.to_thread(translate_texts, texts, target)
        return {'translations': translated}
    except Exception as e:
        return {'translations': []}

@app.get('/api/jobs/{job_id}')
def status(job_id:str):
    if job_id not in jobs:raise HTTPException(404,'Job not found')
    return public_job(jobs[job_id])

@app.websocket('/api/trace/{job_id}')
async def trace(ws:WebSocket,job_id:str):
    try:
        check_origin(ws)
        await authenticate(ws)
    except HTTPException:
        await ws.close(1008)
        return
    await ws.accept()
    if job_id not in jobs:await ws.close(1008);return
    offset=0
    try:
        while True:
            job=jobs[job_id]
            while offset<len(job['events']):
                await ws.send_json({'type':'trace','event':job['events'][offset]});offset+=1
            if job['status'] not in ACTIVE:
                await ws.send_json({'type':job['status'],'result':job.get('result'),'error':job.get('error')});break
            await asyncio.sleep(.1)
    except WebSocketDisconnect:pass
    finally:
        try:await ws.close()
        except RuntimeError:pass

@app.get('/reports/{filename}')
def report(filename:str):
    name=Path(filename);key=name.stem
    if len(key)!=32 or name.suffix not in ('.json','.html','.geojson') or any(c not in '0123456789abcdef' for c in key):raise HTTPException(404)
    path=REPORTS/filename
    if not path.exists():raise HTTPException(404)
    return FileResponse(path,media_type='text/html' if name.suffix=='.html' else 'application/geo+json' if name.suffix=='.geojson' else 'application/json',filename=f'satquery-{filename}',headers={'X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'none'; img-src data:; style-src 'unsafe-inline'; sandbox"})

@app.get('/api/preview/{job_id}/{index}')
def preview(job_id:str,index:int):
    if len(job_id)!=32 or any(c not in '0123456789abcdef' for c in job_id) or not 0<=index<settings.MAX_UPLOADS:raise HTTPException(404)
    path=DATA/f'{job_id}_{index}.png'
    if not path.exists():raise HTTPException(404)
    return FileResponse(path,media_type='image/png')

@app.get('/api/demos')
def demos():
    path=ROOT/'data/demo/manifest.json'
    return json.loads(path.read_text()) if path.exists() else []

@app.post('/api/demos/{demo_id}')
async def demo(demo_id:str,query:str=Query(None)):
    item=next((d for d in demos() if d['id']==demo_id),None)
    if not item:raise HTTPException(404,'Demo not found; run python -m training.make_demo')
    active_query = query.strip() if query and query.strip() else item['query']
    return start([ROOT/p for p in item['paths']],item['options'],item['scenario'],active_query)


@app.post('/api/inspect')
async def inspect_inputs(images:list[UploadFile]=File(...),scenario:str=Form('SINGLE'),options:str=Form('[{"modality":"optical"}]'),query:str=Form('')):
    check_request('inspect',scenario,len(images))
    paths,opts=await uploads(images,options)
    try:
        async with CAPACITY:
            result=await asyncio.to_thread(validate,paths,opts,scenario,query)
        return public_contract(result)
    except Exception as exc:
        return {'validation_status':'INCOMPATIBLE','validation':exc.as_dict() if isinstance(exc,InputError) else
                {'status':'INCOMPATIBLE','code':'INVALID_INPUT','message':str(exc)},'images':[]}
    finally:remove_uploads(paths)


@app.post('/api/jobs/{job_id}/followup')
async def followup(job_id:str,request:Followup):
    parent=jobs.get(job_id)
    if not parent or not parent.get('_paths') or parent['status']!='complete':
        raise HTTPException(409,'Follow-up source is no longer in this session; upload the source imagery again.')
    from gateway.regions import crop_bundle, geographic_box
    if (request.box is None) == (request.bounds is None):
        raise HTTPException(422,'Provide either an image rectangle or geographic bounds.')
    try:
        bundle = await asyncio.to_thread(validate,parent['_paths'],parent['_options'],parent['_scenario'])
        if request.bounds is not None:
            box = geographic_box(bundle, request.bounds)
        else:
            box = request.box
            parent_roi = parent.get('result',{}).get('input',{}).get('images',[{}])[0].get('roi')
            if parent_roi:
                width, height = parent_roi[2]-parent_roi[0], parent_roi[3]-parent_roi[1]
                if not (0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height):
                    raise ValueError('ROI is outside the displayed image.')
                box = [box[0]+parent_roi[0],box[1]+parent_roi[1],box[2]+parent_roi[0],box[3]+parent_roi[1]]
        crop_bundle(bundle,{'box':box})
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
    return start(parent['_paths'],parent['_options'],parent['_scenario'],request.query,
                 roi={'box':box},parent_id=job_id)


@app.get('/api/history')
def history():
    rows=[]
    for path in sorted(REPORTS.glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True):
        try:
            out=json.loads(path.read_text(encoding='utf-8'))
            rows.append({k:out.get(k) for k in ('query_id','query','task','timestamp','trust_score','decision','previews','report_url')})
        except (ValueError,OSError):continue
    return rows


@app.get('/api/benchmarks')
def benchmarks():
    path=ROOT/'evaluation/results.json'
    if not path.exists():return {'status':'BLOCKED','datasets':{},'reason':'Run python -m evaluation.run; no verified current evaluation artifact exists.'}
    out=json.loads(path.read_text(encoding='utf-8'))
    return {k:v for k,v in out.items() if k!='samples'} | {'models':sorted({mode for row in out.get('samples',[]) for mode in row.get('model_modes',[])})}


@app.get('/api/registry')
def registry():
    return yaml.safe_load((ROOT/'configs/tool_registry.yaml').read_text())


@app.post('/api/jobs/{job_id}/context')
async def add_context(job_id:str):
    job=jobs.get(job_id)
    if not job or job['status']!='complete':raise HTTPException(404,'Completed analysis not found in this session')
    from gateway.context import context_for
    result=job['result'];context=await asyncio.to_thread(context_for,result['input']['images'][0])
    result['context']=context
    result['execution_trace'].append({'step':len(result['execution_trace'])+1,'action':'auxiliary_context','status':context['status'],'at':datetime.now(timezone.utc).isoformat(),'analysis_id':job_id,'result':context})
    (REPORTS/f'{job_id}.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    embedded=['data:image/png;base64,'+base64.b64encode((DATA/f'{job_id}_{i}.png').read_bytes()).decode('ascii') for i in range(len(result['previews']))]
    (REPORTS/f'{job_id}.html').write_text(render_html({**result,'embedded_previews':embedded}),encoding='utf-8')
    return result


@app.get('/api/review-queue')
def list_review_queue(decision: str = None, status: str = None, limit: int = 50, offset: int = 0):
    from gateway.review_queue import get_candidates
    return get_candidates(decision=decision, status=status, limit=limit, offset=offset)


@app.get('/api/review-queue/stats')
def review_queue_stats():
    from gateway.review_queue import get_stats
    return get_stats()


@app.post('/api/review-queue/{candidate_id}/confirm')
def confirm_candidate_endpoint(candidate_id: str, notes: str = Form(None)):
    from gateway.review_queue import confirm_candidate
    ok = confirm_candidate(candidate_id, analyst_notes=notes)
    if not ok:
        raise HTTPException(404, 'Candidate not found')
    return {'status': 'confirmed', 'candidate_id': candidate_id}


@app.post('/api/review-queue/{candidate_id}/reject')
def reject_candidate_endpoint(candidate_id: str, notes: str = Form(None)):
    from gateway.review_queue import reject_candidate
    ok = reject_candidate(candidate_id, analyst_notes=notes)
    if not ok:
        raise HTTPException(404, 'Candidate not found')
    return {'status': 'rejected', 'candidate_id': candidate_id}


@app.get('/review-queue')
def review_queue_page():
    path = ROOT / 'gateway' / 'review_dashboard.html'
    return FileResponse(path, media_type='text/html')


if (ROOT/'frontend/dist').exists():
    app.mount('/',StaticFiles(directory=ROOT/'frontend/dist',html=True),name='frontend')
