"""Shared production pipeline, also used verbatim by offline evaluation."""
import importlib,os,re,json,time,uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as InferenceTimeout
from pathlib import Path
from datetime import datetime,timezone
import yaml,httpx
from gateway.validation import validate,public_contract
from verification.engine import verify
from fusion_engine.consensus import combine
from gateway.spatial import spatial_products
from gateway.contracts import checked_output
from gateway.provenance import processing_provenance
from verification.confidence import decision
from gateway.settings import query_text
from gateway.normalization import materialize

ROOT=Path(__file__).resolve().parents[1]
_executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix='satquery-inference')

class RegistryClassifier:
    def classify(self,bundle,query,registry):
        semantic_question = bool(re.search(r"\b(how many|count|what colou?r|which|what type|what kind)\b", query.lower()))
        if bundle['scenario'] == 'SINGLE' and semantic_question:
            tool = next((t for t in registry if t['name'] == 'vqa_caption_v1'), None)
            if tool is not None:return 'VQA', tool
        words=set(re.findall(r'\w+',query.lower()));candidates=[]
        for tool in registry:
            if tool.get('pipeline') == 'specialists':continue
            if bundle['scenario'] not in tool['scenarios']:continue
            if tool.get('modalities') and any(i['modality'] not in tool['modalities'] for i in bundle['images']):continue
            if tool.get('eligibility'):
                module,function=tool['eligibility'].rsplit(':',1)
                if not getattr(importlib.import_module(module),function)(bundle):continue
            for task in tool['tasks']:
                matches=len(words.intersection(tool.get('keywords',{}).get(task,[])))
                score=matches*100+tool['priority']+(1 if task==tool.get('default_task') else 0)
                if matches or task==tool.get('default_task'):candidates.append((score,task,tool))
        if not candidates:raise ValueError('No registered specialist supports these inputs')
        _,task,tool=max(candidates,key=lambda row:row[0]);return task,tool

def run_pipeline(paths,options,scenario,query,params=None,emit=None,classifier=None,analysis_id=None,roi=None,parent_id=None):
    trace=[];started=time.perf_counter();previous=started;timings={};analysis_id=analysis_id or uuid.uuid4().hex
    if len(analysis_id)!=32 or any(c not in '0123456789abcdef' for c in analysis_id):
        from gateway.errors import InputError
        raise InputError('Invalid internal analysis identifier')
    def event(action,**fields):
        nonlocal previous
        now=time.perf_counter()
        item={'step':len(trace)+1,'action':action,'at':datetime.now(timezone.utc).isoformat(),
              'status':'complete','duration_s':round(now-previous,6),'elapsed_s':round(now-started,6),'analysis_id':analysis_id,**fields}
        previous=now
        trace.append(item)
        if emit:emit(item)
    query=query_text(query)
    event('validate_inputs',result='Checking format, bands, modality and spatial grids')
    bundle=validate(paths,options,scenario,query)
    materialize(bundle, ROOT/'data/uploads'/analysis_id/'normalized')
    steps=[s for i in bundle['images'] for s in i['preprocessing_steps']]
    bundle['validation'].update(preprocessing_steps=steps,actions_taken=steps)
    for step in steps:
        event('automatic_preprocessing',result=step)
    if roi:
        from gateway.regions import crop_bundle
        bundle=crop_bundle(bundle,roi)
        event('region_followup',parent_query_id=parent_id,roi=roi,result='Specialists receive only the selected pixel ROI')
    timings['validation_s']=time.perf_counter()-started
    event('validation_complete',result=bundle['validation_status'],notes=bundle['validation_notes'],scenario=scenario)
    from models import cloud_vision
    if cloud_vision.configuration()[2] == 'openrouter' and cloud_vision.enabled():
        from controller.specialist_policy import route
        from controller.cloud_pipeline import run as run_cloud
        route(bundle, query)  # Missing dates/sensors still cannot be guessed by an API.
        event('select_analysis_mode', result='Explicitly configured OpenRouter cloud interpretation; not a named specialist')
        return run_cloud(bundle, query, analysis_id, trace, event, started)
    # Reuse validation, preprocessing, the inference executor and API transport.
    # Legacy models remain an explicit compatibility mode, never a silent fallback.
    if os.environ.get('SATQUERY_PIPELINE', 'specialists') != 'legacy':
        from controller.specialist_policy import route, COMMON, POLICIES
        from models.specialist_runtime import run as run_specialist
        from gateway.analysis_report import normalize, envelope
        task, specialist = route(bundle, query)
        registry = yaml.safe_load((ROOT/'configs/tool_registry.yaml').read_text())['tools']
        selected = next(t for t in registry if t.get('specialist') == specialist and scenario in t['scenarios'])
        if params:
            raise ValueError('Unknown specialist parameter; named runtimes currently accept no public parameters')
        event('classify_intent', result=task, classifier='input_configuration_and_intent_v1')
        event('select_model', model=specialist, reason=f'Validated {scenario} configuration and query intent')
        call = {'task': task, 'specialist': specialist, 'query': query,
                'image_ids': [i['id'] for i in bundle['images']], 'params': {},
                'response_policy': COMMON + '\n' + POLICIES[specialist]}
        raw = None
        try:
            if bundle['validation']['input_quality'] < .15:
                raise ValueError('Input quality is insufficient for semantic inference')
            event('execute', model=specialist, params={})
            pending = _executor.submit(run_specialist, bundle, call)
            try:
                raw = pending.result(timeout=selected['timeout_s'])
            except InferenceTimeout:
                pending.cancel()
                raise
            # Validate before claiming successful execution, preserve exact answer.
            report = normalize(raw, bundle, query, task, specialist, trace)
            event('model_complete', model=raw['model'], result='Specialist output received; semantic correctness unverified')
        except Exception as exc:
            raw = None
            code = 'MODEL_TIMEOUT' if isinstance(exc, InferenceTimeout) else 'MALFORMED_MODEL_OUTPUT' if isinstance(exc, ValueError) else 'MODEL_UNAVAILABLE'
            # Runtime exceptions can contain credentials/paths: expose a stable code only.
            event('model_failure', model=specialist, status='failed', error=code)
            report = normalize(None, bundle, query, task, specialist, trace, error=code)
        grounding_overlay = None
        if raw is not None and task == 'GROUNDING' and bundle['images'][0]['modality'] == 'optical':
            if os.environ.get('SATQUERY_USE_DINO', '1') == '1':
                try:
                    from models.grounding.dino import detect
                    event('execute', model='Grounding DINO', params={'box_threshold': .35, 'text_threshold': .25})
                    pending = _executor.submit(detect, bundle['images'][0], query, .35, .25)
                    boxes = pending.result(timeout=180)
                    report['execution_summary']['models_tools'].append('Grounding DINO')
                    report['execution_summary']['parameters']['Grounding DINO'] = {'box_threshold': .35, 'text_threshold': .25}
                    if boxes:
                        image = bundle['images'][0]
                        grounding_overlay = {'type': 'bbox', 'data': boxes, 'width': image['shape'][1],
                                             'height': image['shape'][0], 'image_id': image['id']}
                        report['spatial_evidence'] = [{'source': 'Grounding DINO', 'kind': 'candidate detection',
                                                       'coordinate_space': 'image pixels', 'overlay': grounding_overlay}]
                        report['execution_summary']['evidence_generated'].append('grounding boxes')
                        report['uncertainty'] = [w for w in report['uncertainty'] if 'no verified grounding overlay' not in w]
                        report['uncertainty'].append('Detector boxes are candidate locations, not verified object counts. Detector scores are uncalibrated.')
                    else:
                        report['uncertainty'].append('No detector boxes exceeded threshold; this does not establish absence.')
                    event('model_complete', model='Grounding DINO', result='Detector execution completed')
                except Exception:
                    if 'pending' in locals(): pending.cancel()
                    report['uncertainty'].append('Grounding tool unavailable; no overlay generated.')
                    event('model_failure', model='Grounding DINO', status='failed', error='GROUNDING_UNAVAILABLE')
            else:
                report['uncertainty'].append('Grounding DINO is disabled by server configuration.')
        report['execution_summary']['warnings'] = report['uncertainty']
        event('report', result='Structured specialist report prepared without additional findings')
        result = envelope(report, bundle, analysis_id, trace, time.perf_counter()-started, raw)
        result['overlay'] = grounding_overlay
        if raw is None:
            result['decision']['code'] = code
        return result
    from models.cloud_vision import enabled as cloud_enabled
    if cloud_enabled():
        from controller.cloud_pipeline import run as run_cloud
        return run_cloud(bundle, query, analysis_id, trace, event, started)
    registry=yaml.safe_load((ROOT/'configs/tool_registry.yaml').read_text())['tools']
    task,selected=(classifier or RegistryClassifier()).classify(bundle,query,registry)
    event('classify_intent',result=task,classifier='registry_keyword_hybrid_v1')
    lookup={t['name']:t for t in registry};plan=[];visiting=set()
    def add(tool):
        if tool['name'] in visiting:raise ValueError('Cyclic tool dependency')
        if tool in plan:return
        visiting.add(tool['name'])
        for dep in tool.get('depends_on',[]):add(lookup[dep])
        visiting.remove(tool['name']);plan.append(tool)
    add(selected);supplied=params or {}
    if set(supplied)-set(selected['params']):raise ValueError('Unknown specialist parameter')
    outputs=[]
    for tool in plan:
        if scenario not in tool['scenarios']:raise ValueError('Dependency does not support scenario')
        bound={}
        for name,spec in tool['params'].items():
            value=supplied.get(name,spec['default'])
            if not isinstance(value,(float,int)) or isinstance(value,bool) or not spec['min']<=value<=spec['max']:raise ValueError(f'Invalid parameter {name}')
            bound[name]=value
        call={'task':task if task in tool['tasks'] else tool.get('default_task',tool['tasks'][0]),'image_ids':[i['id'] for i in bundle['images']], 'query':query,'params':bound}
        event('select_model',model=tool['name'],reason=f'Registry supports {scenario} and {call["task"]}')
        event('execute',model=tool['name'],params=bound)
        inference_start=time.perf_counter()
        try:
            if bundle['validation']['input_quality']<.15:
                raise ValueError('Input quality gate: semantic inference withheld for unusable imagery')
            if os.environ.get('SATQUERY_SERVING')=='http' and tool.get('service'):
                data={**public_contract(bundle),'images':[{k:v for k,v in i.items() if k!='array'} for i in bundle['images']]}
                with httpx.Client(timeout=tool.get('timeout_s',180)) as client:
                    endpoint=json.loads(os.environ.get('SATQUERY_SERVICE_URLS','{}')).get(tool['name'],tool['service'])
                    event('http_request',model=tool['name'],endpoint=endpoint)
                    response=client.post(endpoint,json={'bundle':data,'call':call});response.raise_for_status();raw=response.json()
            else:
                pending=_executor.submit(importlib.import_module(tool['module']).run,bundle,call)
                try: raw=pending.result(timeout=tool.get('timeout_s',180))
                except InferenceTimeout:
                    pending.cancel()
                    raise
            out=checked_output(raw,tool,call,time.perf_counter()-inference_start)
        except Exception as exc:
            code='MODEL_TIMEOUT' if isinstance(exc,(InferenceTimeout,httpx.TimeoutException)) else 'MODEL_UNAVAILABLE'
            out=checked_output({'status':'failed','answer':'Specialist unavailable; remaining evidence paths continue.',
                                'mode':'failed','neural_confidence':0,'claims':[],
                                'errors':[{'code':code,'type':type(exc).__name__,'message':str(exc)}]},tool,call,time.perf_counter()-inference_start)
            event('model_failure',model=tool['name'],status='failed',error=out['errors'])
        event('model_complete',model=tool['name'],mode=out['mode'],result=out['answer']);outputs.append(out)
    timings['inference_s']=sum(o['timing']['inference_s'] for o in outputs)
    verification_started=time.perf_counter()
    event('symbolic_verification',result='Independently checking every structured land-cover/change claim')
    verification=verify(bundle,outputs)
    timings['verification_s']=time.perf_counter()-verification_started
    event('verification_complete',result={'agreement':verification['symbolic_agreement'],'coverage':verification['verification_coverage'],'flags':verification['flags']})
    event('consensus',result='Combining evidence and retaining unresolved contradictions')
    fused=combine(outputs,verification)
    unresolved=any(f.startswith('Optical/SAR disagreement') for f in fused['flags'])
    if unresolved:
        verification['trust_score']=round(verification['trust_score']*.75,4)
        verification['method']+='; unresolved optical/SAR disagreement multiplies trust by 0.75'
        event('consensus_disagreement',result='Unresolved optical/SAR disagreement; trust discounted by 25%')
    statuses=[c['status'] for c in verification['checks']]
    consensus=('partial agreement' if 'supported' in statuses and ('disagrees' in statuses or unresolved) else
               'disagreement' if 'disagrees' in statuses or unresolved else 'agreement' if 'supported' in statuses else 'insufficient evidence')
    temporal_output=next((o for o in outputs if o.get('temporal_evidence')), None)
    agreeing_sources=['change_mask'] if temporal_output else []
    if temporal_output and temporal_output.get('change_vqa', {}).get('confidence', 0) > .4:
        agreeing_sources.append('change_vqa')
    consensus_details={'agreeing_sources':agreeing_sources,
                       'disagreeing_sources':['verification'] if 'disagrees' in statuses else [],
                       'unavailable_sources':['spectral_index'] if temporal_output else [],
                       'score':verification.get('symbolic_agreement'),'label':consensus.upper()}
    temporal_summary=None
    if temporal_output:
        temporal_summary={'visible_change':temporal_output['temporal_evidence']['supported'],
                          'changed_fraction':temporal_output['temporal_evidence']['changed_fraction'],
                          'alignment_quality':temporal_output['temporal_evidence']['alignment_quality'],
                          'claims':verification['checks'],'consensus':consensus_details,
                          'final_trust':verification['trust_score'],'trust_label':'HIGH' if verification['trust_score']>=.8 else 'MODERATE' if verification['trust_score']>=.65 else 'LOW'}
    from controller.scene_analyzer import generate_scene_inventory
    change_overlay = next((o['overlay'] for o in reversed(outputs) if o.get('overlay')), None)
    inventory = generate_scene_inventory(bundle, outputs, query, {**fused, 'trust_score': verification['trust_score'], 'confidence_breakdown': {'final_trust': verification['trust_score']}, 'overlay': change_overlay})
    if temporal_output and change_overlay:
        fused['overlay'] = change_overlay
    elif inventory.get('segmentation_withheld'):
        fused['overlay'] = None
    elif inventory.get('pixel_mask'):
        fused['overlay'] = inventory['pixel_mask']
    fused['pixel_mask'] = inventory.get('pixel_mask')
    fused['composition'] = inventory.get('composition')
    if inventory.get('composition_before'):
        fused['composition_before'] = inventory['composition_before']
    if inventory.get('composition_after'):
        fused['composition_after'] = inventory['composition_after']
    fused['temporal_breakdown'] = inventory.get('temporal_breakdown')
    fused['multi_class_boxes'] = inventory.get('multi_class_boxes')
    fused['present'] = inventory.get('present')
    fused['absent'] = inventory.get('absent')
    if 'short_answer' in inventory:
        fused['short_answer'] = inventory['short_answer']
    if inventory.get('answer'):
        fused['executive_answer'] = inventory['answer']
        fused['answer'] = inventory['answer']

    fusion_summary = None
    if scenario == 'CROSS_MODAL_PAIR':
        sar_img = next((i for i in bundle.get('images', []) if i.get('modality') == 'SAR'), None)
        sar_stats = verification.get('physical_statistics', {}).get(sar_img['id'] if sar_img else 'img2', {}).get('SAR', {})
        fusion_summary = {
            'consensus': consensus,
            'consensus_details': consensus_details,
            'sar_mean_db': sar_stats.get('mean_db'),
            'sar_dark_fraction': sar_stats.get('dark_fraction'),
            'fused_fractions': outputs[0].get('fused_fractions') if outputs else {},
            'flags': fused.get('flags', [])
        }
        fused['short_answer'] = 'CROSS-MODAL OPTICAL + SAR FUSION'
        sar_note = f"SAR microwave radar backscatter averages {sar_stats['mean_db']:.1f} dB ({sar_stats['dark_fraction']:.1%} specular low-backscatter surface water candidate)." if sar_stats.get('mean_db') is not None else "SAR radar backscatter active."
        fused['executive_answer'] = (
            f"Joint Optical and SAR Fusion Analysis: Optical sensors capture visible spectral reflectance, "
            f"while {sar_note} Cross-sensor consensus: {consensus.upper()}. "
            f"Active microwave radar provides all-weather cloud and smoke penetration to corroborate surface geometries."
        )
        fused['answer'] = fused['executive_answer']

    vqa_ans = (fused.get('short_answer') or '').lower()
    vqa_neg = vqa_ans in ('no', 'none', 'nothing', 'neither', 'false')
    ql = query.lower()
    
    # Preserve the evidence score; scene colours cannot raise confidence.
    v_conf = round(verification['neural_confidence'], 4) if any(o['neural_confidence'] > 0 for o in outputs) else None
    if temporal_summary:
        temporal_summary['final_trust'] = verification['trust_score']
        temporal_summary['trust_label'] = 'HIGH' if verification['trust_score']>=.8 else 'MODERATE' if verification['trust_score']>=.65 else 'LOW'

    quality=bundle['validation']['input_quality']
    gate=decision(verification,quality,outputs,consensus)
    if inventory.get('segmentation_withheld'):
        gate={'status':'INSUFFICIENT_EVIDENCE','code':'MODEL_DISAGREEMENT','reason':inventory['answer'],'needed':''}
        verification['trust_score']=0.0
        v_conf=None
    if gate['status'] in ('INSUFFICIENT_EVIDENCE','MODEL_FAILURE'):
        fused['candidate_answer']=fused['answer'];fused['answer']=gate['reason']+' '+gate['needed'];fused['short_answer']=None
    elif gate['status']=='LOW_TRUST': fused['answer']='LOW TRUST — candidate findings only. '+fused['answer']
    from models.reliability import apply_answer_gate
    apply_answer_gate(fused,gate)
    event('answer_gate',result=gate,status=gate['status'])
    event('spatial_measurement',result='Creating full-resolution region measurements and georeferenced exports')
    products=spatial_products(bundle,outputs)
    explanation=f"Evidence-derived trust reflects {verification['verification_coverage']:.0%} independently checkable claim coverage, {quality:.0%} input usability, and {consensus}. Model confidence is uncalibrated and auxiliary."
    opt_gate = None
    if scenario in ('TEMPORAL', 'BITEMPORAL') or len(bundle.get('images', [])) >= 2:
        try:
            from gateway.optical_quality_gate import evaluate_optical_quality_gate
            opt_gate = evaluate_optical_quality_gate(bundle)
            if opt_gate.get('status') in ('review queue', 'suppressed (likely false alarm)', 'low quality'):
                try:
                    from gateway.review_queue import add_candidate
                    add_candidate(
                        analysis_id=analysis_id,
                        query=query,
                        status=opt_gate['status'],
                        gate_summary=opt_gate,
                        change_fraction=temporal_summary['changed_fraction'] if temporal_summary else 0.0,
                        preview_before=f'/api/preview/{analysis_id}/0' if len(bundle.get('images', [])) > 0 else None,
                        preview_after=f'/api/preview/{analysis_id}/1' if len(bundle.get('images', [])) > 1 else None
                    )
                except Exception:
                    pass
        except Exception:
            pass
    spectral_indices = None
    try:
        from gateway.spectral_indices import compute_spectral_indices
        if bundle.get('images'):
            spectral_indices = compute_spectral_indices(bundle['images'][0])
            fused['spectral_indices'] = spectral_indices
    except Exception:
        pass
    event('report',result='Answer, evidence, trust breakdown and trace prepared')
    final_output = {**fused,'query_id':analysis_id,'query':query,'parent_query_id':parent_id,'decision':gate,'consensus':consensus,'consensus_details':consensus_details,'temporal_analysis':temporal_summary,'fusion_analysis':fusion_summary,'optical_quality_gate':opt_gate,'spectral_indices':spectral_indices,'trust_explanation':explanation,
            'provenance':processing_provenance(bundle,outputs),'timings':timings,'task':task,'scenario':scenario,'trust_score':verification['trust_score'],'visual_confidence':v_conf,
            'scene_inventory':inventory,'executive_answer':fused['answer'],
            'visible_features':inventory.get('visible_features',[]),'uncertainties':inventory.get('uncertainties',[]),'present':inventory.get('present',[]),'absent':inventory.get('absent',[]),
            'confidence_breakdown':{'neural':verification['neural_confidence'] if any(o['neural_confidence']>0 for o in outputs) else None,'visual_confidence':v_conf,'symbolic':verification['symbolic_agreement'], 'coverage':verification['verification_coverage'],'evidence_support':verification.get('evidence_support'),'input_quality':quality,'consensus':consensus,'alignment_quality':verification.get('alignment_quality'),'final_trust':verification['trust_score']},
            'verification':verification,'specialists':outputs,'input':public_contract(bundle),'execution_trace':trace,'report_url':None,'spatial_products':products,
            'limitations':['Research system: trust is an evidence heuristic, not a probability of correctness.',
                          'Real water experts use Sen1Floods11 training and validation; transfer to other sensors is not validated.',
                          'Synthetic land-cover and grounding fallbacks are disabled for real uploads.',
                          'The small CDVQA Siamese model saw only two training image pairs; change masks measure appearance changes, not their cause.',
                          'Unstructured VQA suggestions are auxiliary and unverified.']}
    try:
        from gateway.translator import translate_single, translate_texts
        ans_text = final_output.get('executive_answer') or final_output.get('answer') or ''
        vf = [f['name'] if isinstance(f, dict) else str(f) for f in final_output.get('visible_features', [])]
        unc = [u['name'] if isinstance(u, dict) else str(u) for u in final_output.get('uncertainties', [])]
        final_output['translations'] = {
            'hi': {
                'description': translate_single(ans_text, 'hi'),
                'answer': translate_single(ans_text, 'hi'),
                'visible_features': translate_texts(vf, 'hi'),
                'uncertainties': translate_texts(unc, 'hi')
            },
            'bn': {
                'description': translate_single(ans_text, 'bn'),
                'answer': translate_single(ans_text, 'bn'),
                'visible_features': translate_texts(vf, 'bn'),
                'uncertainties': translate_texts(unc, 'bn')
            }
        }
    except Exception as e:
        final_output['translations'] = {}
    return final_output
