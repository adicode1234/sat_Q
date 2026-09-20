from pathlib import Path
import os
import numpy as np
from models.features import pixel_predictions, LABELS

CHECKPOINT=Path(__file__).resolve().parents[1]/'checkpoints/rgb_adapter.npz'
_vilt=None

def vilt_enabled():
    vilt_dir = CHECKPOINT.parent / 'vilt'
    has_weights = (vilt_dir / 'pytorch_model.bin').exists() or (vilt_dir / 'model.safetensors').exists()
    return os.environ.get('SATQUERY_USE_VILT', '1' if has_weights else '0') == '1'


def normalize_vilt_query(query: str) -> str:
    # Keep counts, colour, position and negation intact.
    return query.strip()

def real_image_run(bundle,call):
    import re
    image=bundle['images'][0];q=call['query'].lower()
    if vilt_enabled() and (call.get('task')=='CAPTION' or re.search(r'\b(describe|discribe|caption|summari[sz]e)\b',q)):
        return {'status':'complete','answer':'This local VQA model is not an open-ended caption model. Available image segmentation is shown only when supported; a reliable general description is unavailable.',
                'short_answer':None,'neural_confidence':0,'claims':[],'mode':'caption_capability_unavailable','overlay':None}
    if re.search(r'\b(area|coverage|percentage|percent|ndvi|ndwi|ndbi|hectares)\b', q):
        from models.measurement import run as measure
        out=measure(bundle,call)
        if any(m.get('fraction') is not None for m in out.get('measurements',[])):return out
    has_rgb = all(b in image['bands'] for b in ('red','green','blue'))
    if vilt_enabled() and has_rgb:
        try:
            vqa_q = normalize_vilt_query(call['query'])
            answer,score=pretrained_vqa(image,vqa_q)
            kind={'water':'water','river':'water','lake':'water','stream':'water','flood':'water','forest':'vegetation','grass':'vegetation','trees':'vegetation','tree':'vegetation','buildings':'built_up','building':'built_up'}.get(answer.lower(),'vqa_answer')
            target=next((t for t in ('water','river','lake','trees','tree','forest','vegetation','building','buildings') if t in q),None)
            target_kind={'river':'water','lake':'water','stream':'water','flood':'water','trees':'vegetation','tree':'vegetation','forest':'vegetation','buildings':'built_up','building':'built_up'}.get(target,target)
            claims=[]
            if answer.lower() in ('yes','true') and target_kind:
                claims.append({'type':target_kind,'region':'whole_image','value':answer,'image_id':image['id'],'predicate':'presence'})
            elif kind != 'vqa_answer':
                claims.append({'type':kind,'region':'whole_image','value':answer,'image_id':image['id'],'predicate':'presence'})
            elif target_kind and answer.lower() not in ('no', 'false', 'none'):
                claims.append({'type':target_kind,'region':'whole_image','value':answer,'image_id':image['id'],'predicate':'presence'})
            elif answer.lower() not in ('no', 'false', 'none'):
                claims.append({'type':'vqa_answer','region':'whole_image','value':answer,'image_id':image['id']})
            # Present a clear, direct answer without robotic system caveats
            clean_ans = answer.capitalize() if answer else answer
            return {'status':'complete','answer':f'Candidate visual answer: {clean_ans}. This model score is uncalibrated.',
                    'short_answer':answer,'neural_confidence':min(score,0.95),'claims':claims,
                    'mode':'real_image_vilt_auxiliary','overlay':None}
        except (ImportError,OSError,RuntimeError,ValueError) as exc:
            reason=type(exc).__name__
    else:reason='missing enabled VQA checkpoint or named RGB bands'
    return {'status':'complete',
            'answer':'No suitable semantic model for this input: '+reason+'. Supply known spectral bands for measurements or a supported visual checkpoint. Synthetic land-cover percentages are disabled for real uploads.',
            'neural_confidence':0,'claims':[],'mode':'real_image_capability_unavailable','overlay':None}

def pretrained_vqa(image, query):
    global _vilt
    import torch
    from PIL import Image
    from transformers import ViltProcessor,ViltForQuestionAnswering
    from gateway.validation import rgb
    if _vilt is None:
        torch.set_num_threads(4)
        path=os.environ.get('SATQUERY_VILT_PATH',str(CHECKPOINT.parent/'vilt'))
        model=ViltForQuestionAnswering.from_pretrained(path,local_files_only=True).eval()
        adapter=CHECKPOINT.parent/'vilt_lora'
        if (adapter/'adapter_config.json').exists():
            from peft import PeftModel
            model=PeftModel.from_pretrained(model,adapter,local_files_only=True).eval()
        _vilt=(ViltProcessor.from_pretrained(path,local_files_only=True),model)
    p,m=_vilt
    with torch.inference_mode():
        logits=m(**p(Image.fromarray(rgb(image)),query,return_tensors='pt')).logits
        k=int(logits.argmax(-1))
        pred_label = m.config.id2label[k]
        raw_sig = float(logits.sigmoid()[0, k])
        score = raw_sig
    return pred_label, score

def run(bundle, call):
    image=bundle['images'][0]
    if image['modality']=='SAR':
        from verification.engine import summaries
        from gateway.spatial import pack_mask
        from models.change_mask.model import encode
        stats,_=summaries(bundle);radar=stats[image['id']].get('SAR',{})
        dark_frac = radar.get('dark_fraction')
        arr = image['array'][0]
        finite = arr[np.isfinite(arr)]
        if radar.get('mean_db') is not None and dark_frac is not None:
            answer=(f"SAR measurement answer: mean backscatter {radar['mean_db']:.2f} dB, standard deviation {radar['std_db']:.2f} dB; "
                    f"{dark_frac:.1%} of valid pixels are below -17 dB. Dark returns typically indicate smooth surfaces (like calm water); low backscatter cannot uniquely identify water.")
            power_db = 10 * np.log10(np.where(arr > 0, arr, np.nan)) if image.get('sar_units') == 'linear' else arr
            w_mask = np.isfinite(power_db) & (power_db < -17.0)
            overlay = encode(w_mask, image['id'])
            overlay['label'] = 'SAR smooth-surface proxy'
            measurements=[{'image_id':image['id'],'index':'SAR dark-return proxy',
                           'fraction':dark_frac,'mean_db':radar['mean_db'],'std_db':radar['std_db']}]
            return {'answer':answer,'neural_confidence':0,'claims':[],'measurements':measurements,
                    'short_answer':None,
                    'mode':'deterministic_sar_measurement_vqa','overlay':overlay,'raw_mask':pack_mask(w_mask)}
        else:
            lo,median,hi=np.percentile(finite,[10,50,90]) if finite.size else (0,0,0)
            answer=(f'SAR intensity relative visual summary: pixel-value percentiles P10={lo:.3g}, median={median:.3g}, P90={hi:.3g}. '
                    'Values indicate relative brightness and structural texture.')
            return {'answer':answer,'neural_confidence':0,'claims':[],'measurements':[],
                    'mode':'deterministic_sar_measurement_vqa','overlay':None}
    if image.get('source_type') not in (None,'synthetic_demo'):
        return real_image_run(bundle,call)
    if not all(b in image['bands'] for b in ('red','green','blue')):
        return {'answer':'This specialist requires named red, green and blue optical bands. Available physical measurements appear in the evidence panel; no RGB land-cover estimate is made.',
                'neural_confidence':0,'claims':[],'mode':'unsupported_rgb_input','overlay':None}
    try:
        from models.rgb_water import predict_segmentation
        mapped, _, seg_stats, seg_valid = predict_segmentation(image)
        valid_count = max(int(seg_valid.sum()), 1)
        fractions = {
            'water': float((mapped == 2)[seg_valid].sum() / valid_count),
            'vegetation': float((mapped == 1)[seg_valid].sum() / valid_count),
            'built_up': float((mapped == 3)[seg_valid].sum() / valid_count),
            'other': float(((mapped == 0) | (mapped == 4))[seg_valid].sum() / valid_count)
        }
        confidence = np.full(seg_valid.shape, 0.6)
        mode = 'calibrated_multispectral_segmentation' if ('nir' in image.get('bands', [])) else 'calibrated_optical_segmentation'
        mask = np.where(mapped == 2, 0, np.where(mapped == 1, 1, np.where(mapped == 3, 2, 3)))
        valid = seg_valid
    except Exception:
        mask,confidence,mode=pixel_predictions(image,CHECKPOINT)
        valid=mask>=0
        fractions={name:float((mask[valid]==i).mean()) for i,name in enumerate(LABELS)}
    target=next((name for name in LABELS[:3] if name.replace('_',' ') in call['query'].lower() or name in call['query'].lower()),None)
    claims=[{'type':k,'region':'whole_image','value':'estimated area fraction','fraction':v,'image_id':image['id'],'sampling_basis':'valid_rgb'} for k,v in fractions.items() if k!='other']
    summary=', '.join(f'{k.replace("_"," ")} {v:.0%}' for k,v in fractions.items())
    answer=f'Visual land-cover estimation over valid RGB pixels ({valid.mean():.1%} of the image): {summary}. '
    raw=None;raw_score=None
    if os.environ.get('SATQUERY_USE_VILT')=='1' and call['task']=='VQA':
        try:
            raw,score=pretrained_vqa(image,call['query']);raw_score=score
            adapted=(CHECKPOINT.parent/'vilt_lora/adapter_config.json').exists()
            answer+=f'Auxiliary visual scan suggests: {raw}. '
            mode+=' + '+('vrsbench_lora_vilt_auxiliary' if adapted else 'general_vilt_auxiliary')
            kind={'water':'water','river':'water','lake':'water','forest':'vegetation','grass':'vegetation','trees':'vegetation','buildings':'built_up'}.get(raw.lower(),'vqa_answer')
            claims.append({'type':kind,'region':'whole_image','value':raw,'image_id':image['id'],'predicate':'presence'})
        except Exception as exc:
            pass
            
    overlay=None
    if target:
        answer+=f'For your {target.replace("_"," ")} question: {fractions[target]:.1%} candidate coverage. '
        ys,xs=np.where(mask==LABELS.index(target))
        if len(xs):overlay={'type':'bbox','data':[{'box':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],'label':target+' candidate extent'}],
                            'width':mask.shape[1],'height':mask.shape[0],'image_id':image['id']}
    return {'answer':answer,'neural_confidence':min(float(confidence[valid].mean()),.6,raw_score if raw_score is not None else 1),
            'claims':claims,'mode':mode,'raw_vqa':raw,'raw_vqa_confidence':raw_score,'fractions':fractions,'overlay':overlay}
