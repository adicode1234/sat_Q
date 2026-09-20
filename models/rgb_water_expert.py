"""RGB water classifier trained on labelled Sen1Floods11 renderings."""
from pathlib import Path
from functools import lru_cache
import numpy as np
def uniform_filter(a,size=5,mode='reflect'):
    radius=size//2
    padded=np.pad(a,((radius,radius),(radius,radius)),mode=mode).astype('float64')
    c=np.pad(padded,((1,0),(1,0))).cumsum(0).cumsum(1)
    return ((c[size:,size:]-c[:-size,size:]-c[size:,:-size]+c[:-size,:-size])/(size*size)).astype('float32')
ROOT=Path(__file__).resolve().parents[1]
def features(rgb):
    a=(rgb/255).astype('float32');mean=np.stack([uniform_filter(a[...,i],size=5,mode='reflect') for i in range(3)],-1)
    std=np.sqrt(np.maximum(np.stack([uniform_filter(a[...,i]**2,size=5,mode='reflect') for i in range(3)],-1)-mean**2,0))
    chroma=a/(a.sum(-1,keepdims=True)+1e-4)
    return np.concatenate([a,mean,std,chroma],-1)
@lru_cache(maxsize=1)
def checkpoint():
    with np.load(ROOT/'models/checkpoints/rgb_water_real.npz') as f:return {k:f[k].copy() for k in f.files}
def predict(rgb,valid):
    weights=checkpoint();x=features(rgb)[valid];values=[]
    for chunk in range(0,len(x),65536):
        z=(x[chunk:chunk+65536]-weights['mean'])/weights['std']
        h=np.maximum(z@weights['w1']+weights['b1'],0);logits=(h@weights['w2']+weights['b2'])/weights['temperature']
        logits-=logits.max(-1,keepdims=True);e=np.exp(logits);values.append(e[:,1]/e.sum(-1))
    p=np.full(valid.shape,np.nan,dtype='float32');p[valid]=np.concatenate(values)
    return p,float(weights['threshold'])
