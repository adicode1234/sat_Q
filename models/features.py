"""RGB-only specialist features, deliberately independent of spectral verifier."""
import numpy as np
from gateway.validation import rgb

LABELS = ['water','vegetation','built_up','other']

def features(image):
    arr=rgb(image).astype('float32')/255
    r,g,b=arr.transpose(2,0,1)
    return np.stack([r,g,b,g-r,b-r,arr.mean(2),arr.std(2)],axis=-1)

def pixel_predictions(image, checkpoint):
    x=features(image)
    indices=[image['bands'].index(b) for b in ('red','green','blue')]
    valid=np.isfinite(image['array'][indices]).all(axis=0)
    if not valid.any():raise ValueError('No pixels have three valid RGB bands')
    if checkpoint.exists():
        p=np.load(checkpoint)
        hidden=np.tanh(x@p['w1']+p['b1'])
        logits=hidden@p['w2']+p['b2']
        logits-=logits.max(axis=-1,keepdims=True)
        prob=np.exp(logits); prob/=prob.sum(axis=-1,keepdims=True)
        return np.where(valid,prob.argmax(-1),-1),np.where(valid,prob.max(-1),0),'adapted_tiny_rgb_mlp'
    # Explicit untrained fallback, never called a neural model.
    r,g,b=x[...,:3].transpose(2,0,1)
    mask=np.full(r.shape,3)
    mask[(b>r*1.2)&(b>g*.95)]=0
    mask[(g>r*1.15)&(g>b*1.1)]=1
    mask[(np.abs(r-g)<.1)&(np.abs(g-b)<.1)&(r>.35)]=2
    return np.where(valid,mask,-1),np.zeros(r.shape),'untrained_rgb_heuristic'
