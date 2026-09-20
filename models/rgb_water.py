"""Local learned RGB segmentation. Scores are uncalibrated on new sensors."""
from functools import lru_cache
from pathlib import Path
import threading
import numpy as np
import torch
from transformers import SegformerForSemanticSegmentation

ROOT=Path(__file__).resolve().parents[1]
CHECKPOINT=ROOT/'models/checkpoints/rgb_water_segformer'
_lock=threading.Lock()
MEAN=np.array([.485,.456,.406],dtype='float32')
STD=np.array([.229,.224,.225],dtype='float32')

@lru_cache(maxsize=1)
def get_model():
    torch.set_num_threads(4)
    return SegformerForSemanticSegmentation.from_pretrained(str(CHECKPOINT),local_files_only=True).eval()

def pixels(image):
    bands=image.get('bands',[])
    if image.get('modality')!='optical' or not all(b in bands for b in ('red','green','blue')):
        raise ValueError('RGB segmentation requires named red, green and blue channels')
    a=image['array'][[bands.index(b) for b in ('red','green','blue')]].transpose(1,2,0)
    valid=np.isfinite(a).all(-1)
    if not valid.any():raise ValueError('No valid RGB pixels')
    if image.get('raster_metadata',{}).get('format') in ('PNG','JPEG'):
        pass # display RGB is already normalized; it is not physical reflectance
    elif image.get('radiometry',{}).get('reflectance_scale_known') and image.get('source_type')!='synthetic_demo':
        a=a/.3 # same fixed Sentinel reflectance rendering used by the image preview
    elif float(np.max(a[valid]))>1:
        if float(np.max(a[valid]))>255:raise ValueError('Declare reflectance scaling for high-bit-depth optical imagery')
        a=a/255.
    return np.clip(np.nan_to_num(a),0,1).astype('float32')*255,valid

def supports(bundle):
    try:
        pixels(bundle['images'][0])
        return (CHECKPOINT/'model.safetensors').exists()
    except (ValueError,KeyError,IndexError):return False

def predict_segmentation(image):
    # Cache within this validated request only, never by filename across uploads.
    a,valid=pixels(image);h,w=valid.shape
    tile=512;stride=384
    starts=lambda n:list(range(0,max(n-tile,0)+1,stride))+([n-tile] if n>tile and (n-tile)%stride else [])
    totals=np.zeros((6,h,w),dtype='float32');counts=np.zeros((h,w),dtype='float32')
    with _lock,torch.inference_mode():
        model=get_model()
        for y in starts(h):
            for x in starts(w):
                patch=a[y:y+tile,x:x+tile];ph,pw=patch.shape[:2]
                tensor=torch.from_numpy(((patch/255.-MEAN)/STD).transpose(2,0,1).copy())[None]
                # Preserve pixel geometry; padding only meets encoder minimum size.
                tensor=torch.nn.functional.pad(tensor,(0,max(0,32-pw),0,max(0,32-ph)),mode='replicate')
                logits=model(pixel_values=tensor).logits
                prob=torch.nn.functional.interpolate(logits,size=tensor.shape[-2:],mode='bilinear',align_corners=False).softmax(1)[0,:,:ph,:pw].numpy()
                totals[:,y:y+ph,x:x+pw]+=prob;counts[y:y+ph,x:x+pw]+=1
    totals/=counts[None]
    labels=totals.argmax(0)
    # Source classes: background, water, building, road, bridge, vegetation.
    mapped=np.array([0,2,3,4,4,1],dtype='uint8')[labels];mapped[~valid]=0
    water_prob=totals[1].copy();water_prob[~valid]=np.nan
    model_name='pretrained_segformer_rgb'
    reliability=None
    if (ROOT/'models/checkpoints/rgb_water_real.npz').exists() and image.get('source_type')!='synthetic_demo' and 'nir' not in image.get('bands',[]):
        from models.rgb_water_expert import predict as predict_water
        water_prob,threshold=predict_water(a,valid)
        # Binary expert owns water decisions; retained classes come from SegFormer.
        from models.reliability import water_agreement
        expert_water=(water_prob>=threshold)&valid&(mapped!=3)&(mapped!=4)
        seg_water=(mapped==2)&valid
        reliability=water_agreement(seg_water,expert_water,valid)
        if reliability['reliable']:
            combined_water=seg_water|expert_water
        else:
            combined_water=seg_water if seg_water.sum()>0 else (seg_water&expert_water)
        mapped[mapped==2]=0
        mapped[combined_water]=2
        model_name='sen1floods11_rgb_water + pretrained_segformer_rgb'
    stats={name:float(((mapped==label)&valid).sum()/valid.sum()*100) for name,label in [('other',0),('veg',1),('water',2),('built',3),('road',4)]}
    stats.update(model=model_name,mean_model_score=float(totals.max(0)[valid].mean()),calibrated=False,water_reliability=reliability)
    return mapped,water_prob,stats,valid

def predict(image,tile=512,overlap=128):
    _,p,_,valid=predict_segmentation(image)
    return p,valid
