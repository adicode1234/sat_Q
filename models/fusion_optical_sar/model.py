import numpy as np
import os,threading
from pathlib import Path
from models.vqa_caption.model import run as optical_run
from models.features import LABELS
from models.change_mask.model import encode
from gateway.spatial import pack_mask, heatmap

_model=None
_lock=threading.Lock()

def learned_fusion(optical,sar):
    global _model
    import torch
    from models.fusion_optical_sar.network import CrossModalNet,tensors
    with _lock:
        if _model is None:
            torch.set_num_threads(4);m=CrossModalNet()
            m.load_state_dict(torch.load(Path(__file__).resolve().parents[1]/'checkpoints/fusion_cross_attention/weights.pt',map_location='cpu',weights_only=True))
            _model=m.eval()
    with torch.inference_mode():
        probs=_model(*tensors(optical,sar)).softmax(1)
        probs=torch.nn.functional.interpolate(probs,size=optical['shape'],mode='bilinear',align_corners=False)[0]
        confidence,mask=probs.max(0)
    valid=np.isfinite(optical['array'][[optical['bands'].index(b) for b in ('red','green','blue')]]).all(0)&np.isfinite(sar['array'][0])
    if sar['sar_units']=='linear':valid &= sar['array'][0]>0
    if not valid.any():raise ValueError('No common calibrated optical/SAR pixels')
    return mask.numpy(),confidence.numpy(),valid

def run(bundle,call):
    optical=next(i for i in bundle['images'] if i['modality']=='optical')
    sar=next(i for i in bundle['images'] if i['modality']=='SAR')
    out=optical_run({**bundle,'images':[optical]},call)
    a=optical['array'];bands=optical['bands']; cloud=None
    if all(b in bands for b in ['red','green','blue']):
        r=a[[bands.index(b) for b in ['red','green','blue']]]
        if np.nanmax(r)<=1.5 and np.nanmin(r)>=0:
            cloud=float(((r.mean(0)>.8)&(r.std(0)<.08)).mean())
    out['cloud_proxy']=cloud
    out['answer']+=' Optical and SAR evidence are evaluated separately before consensus. '
    out['mode']+=' + optical_sar_proxy_fusion'
    if sar['sar_units'] in ('db','linear'):
        v=sar['array'][0]
        if sar['sar_units']=='linear':v=10*np.log10(np.where(v>0,v,np.nan))
        valid=np.isfinite(v);fraction=float((v[valid]<-17).mean()) if valid.any() else 0
        out['sar_water_proxy']=fraction
        # SAR is deterministic supporting evidence, not a neural claim. Do not
        # verify this proxy against the identical calculation and inflate trust.
    if optical.get('source_type') not in (None,'synthetic_demo'):
        out['answer']+=' Synthetic-trained joint classification is disabled for real uploads. For water, the registry uses the real-trained expert when radiometry and bands are compatible.'
        return out
    if os.environ.get('SATQUERY_USE_FUSION_MODEL','1')=='1' and sar['sar_units'] in ('db','linear') and all(b in bands for b in ('red','green','blue')):
        try:
            mask,confidence,valid=learned_fusion(optical,sar)
            fractions={name:float((mask[valid]==i).mean()) for i,name in enumerate(LABELS)}
            out['fused_fractions']=fractions
            out['mode']+=' + synthetic_trained_cross_attention'
            out['answer']+=' Synthetic-trained cross-attention joint estimates: '+', '.join(f'{k} {v:.0%}' for k,v in fractions.items())+'. These weights have no validated real-world fusion performance.'
            out['neural_confidence']=min(out['neural_confidence'],float(confidence[valid].mean()),.6)
            # Keep the optical-only claims for independent cross-modal disagreement.
            # Fused estimates are checked against optical physical bands too.
            rgb_valid=np.isfinite(a[[bands.index(b) for b in ('red','green','blue')]]).all(0)
            if np.array_equal(valid,rgb_valid):
                out['claims'] += [{'type':k,'region':'whole_image','value':'cross-attention fused fraction','fraction':v,'image_id':optical['id'],'sampling_basis':'valid_rgb'} for k,v in fractions.items() if k!='other']
            else:
                out['claims'].append({'type':'fusion_estimate','region':'whole_image','value':'Fused fractions cover only common optical/SAR valid pixels; incomplete spatial coverage remains unverified','image_id':optical['id']})
            out['overlay']=encode((mask==0)&valid);out['overlay']['image_id']=optical['id']
            out['overlay']['label']='Synthetic-trained fusion water candidates (not ground truth)'
            out['raw_mask']=pack_mask((mask==0)&valid)
            out['heatmap']=heatmap(np.where(valid,1-confidence,np.nan),optical['id'],'1 minus maximum synthetic-trained model softmax score; uncalibrated uncertainty indicator')
        except (ImportError,OSError,RuntimeError,ValueError,KeyError) as exc:
            out['answer']+=f' Learned fusion unavailable ({type(exc).__name__}); disclosed proxy fusion remains active.'
    return out
