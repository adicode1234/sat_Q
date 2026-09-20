import numpy as np
import os,json,threading
from pathlib import Path
from models.change_mask.model import encode
from gateway.spatial import pack_mask, heatmap

_model=None
_lock=threading.Lock()

def learned_answer(images,query):
    global _model
    import torch
    from models.change_vqa.network import SiameseVQA,image_tensor,question_tensor
    folder=Path(__file__).resolve().parents[1]/'checkpoints/change_siamese'
    with _lock:
        if _model is None:
            torch.set_num_threads(4);config=json.loads((folder/'config.json').read_text())
            model=SiameseVQA(len(config['vocabulary'])+2,len(config['answers']))
            model.load_state_dict(torch.load(folder/'weights.pt',map_location='cpu',weights_only=True));model.eval()
            _model=(model,config)
    model,config=_model
    with torch.inference_mode():
        a,b=[image_tensor(i)[None] for i in images];q=question_tensor(query,config['vocabulary'])[None]
        scores=model(a,b,q).softmax(-1)[0];index=int(scores.argmax())
    return config['answers'][index],float(scores[index])

def run(bundle,call):
    a,b=bundle['images']; x=a['array']; y=b['array']
    shared=np.isfinite(x)&np.isfinite(y)
    if not shared.all(axis=0).any():raise ValueError('Temporal images have no shared valid pixels; change cannot be measured')
    vals=np.concatenate([x[shared],y[shared]])
    lo,hi=np.percentile(vals,[2,98]) if vals.size else (0,1)
    delta=np.mean(np.abs(np.nan_to_num(y-x))/(max(float(hi-lo),1e-6)),axis=0)
    valid=shared.all(axis=0); mask=(delta>call['params']['threshold'])&valid
    fraction=float(mask.sum()/max(valid.sum(),1))
    result={'answer':f'Candidate appearance change affects {fraction:.1%} of comparable pixels between {a["date"] or "the before image"} and {b["date"] or "the after image"}. Illumination, season and acquisition differences can also produce this signal.',
            'neural_confidence':0,'claims':[{'type':'change','region':'whole_image','value':'candidate fraction','fraction':fraction,'image_id':a['id']}],
            'mode':'deterministic_change_fallback_no_trained_siamese_model','overlay':encode(mask), 'change_fraction':fraction,
            'changed_pixel_count':int(mask.sum()),'comparable_pixel_count':int(valid.sum()),'raw_mask':pack_mask(mask),
            'heatmap':heatmap(np.where(valid,np.clip(delta,0,1),np.nan),b['id'],'Heuristic normalized appearance difference; not probability or calibrated uncertainty')}
    checkpoint=Path(__file__).resolve().parents[1]/'checkpoints/change_siamese/weights.pt'
    if os.environ.get('SATQUERY_USE_CHANGE_MODEL','1')=='1' and checkpoint.exists() and all(i['modality']=='optical' and all(b in i['bands'] for b in ('red','green','blue')) for i in (a,b)):
        try:
            answer,confidence=learned_answer([a,b],call['query'])
            result.update(short_answer=answer,neural_confidence=min(confidence,.6),raw_neural_confidence=confidence,mode='cdvqa_tiny_siamese_vqa + deterministic_candidate_mask')
            result['answer']=f'Small-scale CDVQA Siamese model response: {answer}. This question-specific suggestion is unverified. '+result['answer']
            result['claims'].append({'type':'change_vqa_answer','value':answer,'region':'whole_image','image_id':a['id']})
            result['training_scope']='48 questions from only two training image pairs; not a generalization claim'
        except (ImportError,OSError,RuntimeError,ValueError,KeyError) as exc:
            result['answer']+=f' Trained change-VQA unavailable ({type(exc).__name__}); deterministic fallback is active.'
    return result
