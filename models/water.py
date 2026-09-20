"""Real-data-trained water experts with input checks and validation temperature.

No per-image stretching or symbolic indices are used as model inputs.
"""
import json
from pathlib import Path
from functools import lru_cache
import numpy as np
from models.change_mask.model import encode
from gateway.spatial import pack_mask
ROOT=Path(__file__).resolve().parents[1]
OPTICAL=['blue','green','red','nir','swir']

def supports(bundle):
    if any(i.get('source_type')=='synthetic_demo' for i in bundle['images']):return False
    kinds={i['modality'] for i in bundle['images']};kind='joint' if len(kinds)>1 else 'sar' if 'SAR' in kinds else 'optical'
    if not (ROOT/f'models/checkpoints/water_real/{kind}.npz').exists():return False
    try:inputs(bundle['images'],kind);return True
    except (ValueError,KeyError):return False

def inputs(images,kind):
    pieces=[];target=None
    if kind in ('optical','joint'):
        o=next((i for i in images if i['modality']=='optical'),None)
        if not o or not all(b in o['bands'] for b in OPTICAL):raise ValueError('Water model needs blue, green, red, NIR and SWIR bands')
        a=o['array'][[o['bands'].index(b) for b in OPTICAL]]
        if not o.get('radiometry',{}).get('reflectance_scale_known'):raise ValueError('Water model needs declared optical reflectance scaling or raster scale metadata')
        pieces.append(a);target=o
    if kind in ('sar','joint'):
        s=next((i for i in images if i['modality']=='SAR'),None)
        if not s or not all(b in s['bands'] for b in ('vv','vh')):raise ValueError('Trained radar water expert needs VV and VH; other polarizations use measurement tools')
        if s['sar_units'] not in ('db','linear'):raise ValueError('SAR units/calibration unknown; raw DN cannot enter the trained power model')
        a=s['array'][[s['bands'].index(b) for b in ('vv','vh')]]
        if s['sar_units']=='linear':a=10*np.log10(np.where(a>0,a,np.nan))
        # Neighborhood texture features, never substituted for physical backscatter.
        def local_mean(v):
            p=np.pad(v,((0,0),(2,2),(2,2)),mode='reflect')
            c=np.pad(p,((0,0),(1,0),(1,0))).cumsum(1).cumsum(2)
            return (c[:,5:,5:]-c[:,:-5,5:]-c[:,5:,:-5]+c[:,:-5,:-5])/25
        finite=np.isfinite(a);safe=np.where(finite,a,0).astype('float64');n=local_mean(finite.astype(float))
        mean=local_mean(safe)/np.maximum(n,1e-6)
        std=np.sqrt(np.maximum(local_mean(safe**2)/np.maximum(n,1e-6)-mean**2,0))
        a=np.where((a>-60)&(a<30),a,np.nan)
        pieces.append(np.concatenate([a,mean,std]).astype('float32'));target=target or s
    x=np.concatenate(pieces).transpose(1,2,0).astype('float32')
    valid=np.isfinite(x).all(-1)
    if kind in ('optical','joint'):valid &= ((x[...,:5]>=-.1)&(x[...,:5]<=1.6)).all(-1)
    if not valid.any():raise ValueError('No pixels satisfy the model radiometric domain')
    return x,valid,target

@lru_cache(maxsize=3)
def checkpoint(kind):
    folder=ROOT/'models/checkpoints/water_real'
    with np.load(folder/f'{kind}.npz') as f:weights={k:f[k].copy() for k in f.files}
    return weights,json.loads((folder/'evaluation.json').read_text())[kind]

def predict(images,kind):
    x,valid,target=inputs(images,kind);w,metrics=checkpoint(kind)
    z=(x[valid]-w['mean'])/w['std'];prob=np.full(valid.shape,np.nan,dtype='float32')
    values=[]
    for start in range(0,len(z),65536):
        h=np.maximum(z[start:start+65536]@w['w1']+w['b1'],0)
        logits=(h@w['w2']+w['b2'])/w['temperature'];logits-=logits.max(-1,keepdims=True)
        exp=np.exp(logits);values.append(exp[:,1]/exp.sum(-1))
    prob[valid]=np.concatenate(values)
    return prob,valid,target,metrics

def run(bundle,call):
    kinds={i['modality'] for i in bundle['images']}
    kind='joint' if len(kinds)>1 else 'sar' if 'SAR' in kinds else 'optical'
    try:prob,valid,image,metrics=predict(bundle['images'],kind)
    except (ValueError,OSError,StopIteration) as exc:
        return {'status':'unavailable','answer':str(exc),'mode':'real_water_model_unavailable','neural_confidence':0,'claims':[],'overlay':None}
    mask=(prob>=metrics.get('threshold',.5))&valid;fraction=float(mask.sum()/valid.sum());confidence=float(np.maximum(prob[valid],1-prob[valid]).mean())
    # Validation IoU constrains reliability; test labels never set live scores.
    score=min(confidence,metrics['validation_calibrated']['iou']);coverage=float(valid.mean())
    out={'answer':f'Real-data-trained {kind} water expert estimates {fraction:.1%} water candidates over {coverage:.1%} usable image coverage. '
                   'This estimates water extent, not flood causation. Weights were trained on Sen1Floods11; transfer to other sensors is not validated.',
         'neural_confidence':score,'raw_neural_confidence':confidence,'fractions':{'water':fraction},
         'claims':[{'type':'water','region':'whole_image','fraction':fraction,'value':'real-data-trained water fraction','image_id':image['id'],'sampling_basis':'model_valid','model_valid_coverage':coverage}],
         'mode':f'sen1floods11_{kind}_water_mlp','overlay':encode(mask,image['id']),'raw_mask':pack_mask(mask),'valid_mask':pack_mask(valid),
         'calibration':{'method':'temperature fit on separate validation chips','temperature':metrics['temperature'],'domain':'Sen1Floods11','transfer_calibrated':False},
         'model_validation':metrics['test'],'prediction_coverage':coverage,'limitations':['Limited real-data water model; not general land-cover segmentation.']}
    out['overlay']['label']='Real-data-trained water candidates'
    if kind=='joint':
        estimates={}
        for k in ('optical','sar'):
            p,v,_,km=predict(bundle['images'],k);estimates[k]=float(((p>=km.get('threshold',.5))&v).sum()/v.sum())
        out['modality_estimates']=estimates
        out['answer']+=f" Independent optical water estimate {estimates['optical']:.1%}; radar estimate {estimates['sar']:.1%}."
        if abs(estimates['optical']-estimates['sar'])>.2:
            out['answer']+=' Optical/SAR predictions disagree; cloud, shadow, smooth ground or acquisition differences need review.'
            out['cross_modal_disagreement']=True
    return out
