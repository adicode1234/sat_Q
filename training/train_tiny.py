"""CPU fallback: actually train an RGB MLP on synthetic remote-sensing colors.

This demonstrates adaptation mechanics, NOT real-world remote-sensing accuracy.
Train/test noise seeds are disjoint; spectra/palette are shared, a serious limitation.
"""
import json
from pathlib import Path
import numpy as np
from training.make_demo import scene
from gateway.validation import rgb
from models.features import features,LABELS
ROOT=Path(__file__).resolve().parents[1]

def main():
    rng=np.random.default_rng(12);xs=[];ys=[]
    for seed in range(16):
        a,y=scene(seed,64);image={'array':a,'bands':['red','green','blue','nir','swir']}
        xs.append(features(image).reshape(-1,7));ys.append(y.ravel())
    x=np.concatenate(xs);y=np.concatenate(ys);indices=rng.choice(len(x),8192,replace=False);x=x[indices];y=y[indices]
    w1=rng.normal(0,.15,(7,16));b1=np.zeros(16);w2=rng.normal(0,.15,(16,4));b2=np.zeros(4)
    folder=ROOT/'models/checkpoints';folder.mkdir(parents=True,exist_ok=True)
    np.savez(folder/'rgb_base.npz',w1=w1,b1=b1,w2=w2,b2=b2)
    loss=[]
    for step in range(300):
        ids=rng.choice(len(x),512,replace=False);batch=x[ids];target=y[ids]
        h=np.tanh(batch@w1+b1);z=h@w2+b2;z-=z.max(1,keepdims=True);p=np.exp(z);p/=p.sum(1,keepdims=True)
        loss.append(float(-np.log(p[np.arange(len(ids)),target]+1e-8).mean()))
        dz=p;dz[np.arange(len(ids)),target]-=1;dz/=len(ids)
        dh=(dz@w2.T)*(1-h*h)
        w2-=.15*h.T@dz;b2-=.15*dz.sum(0);w1-=.15*batch.T@dh;b1-=.15*dh.sum(0)
    np.savez(folder/'rgb_adapter.npz',w1=w1,b1=b1,w2=w2,b2=b2)
    from models.features import pixel_predictions
    a,y=scene(500,96);image={'array':a,'bands':['red','green','blue','nir','swir']}
    before,_,_=pixel_predictions(image,folder/'rgb_base.npz');after,_,_=pixel_predictions(image,folder/'rgb_adapter.npz')
    evidence={'mode':'SYNTHETIC SMALL-SCALE TRAINING, NOT BENCHMARK ACCURACY','architecture':'7 RGB features → tanh(16) → 4 land-cover classes',
              'training_samples':8192,'synthetic_scenes':16,'steps':300,'seed':12,
              'query':'What land cover is visible in this image?',
              'before':{'accuracy_on_synthetic_holdout':float((before==y).mean()),'answer':{k:float((before==i).mean()) for i,k in enumerate(LABELS)}},
              'after':{'accuracy_on_synthetic_holdout':float((after==y).mean()),'answer':{k:float((after==i).mean()) for i,k in enumerate(LABELS)}},
              'loss_first':loss[0],'loss_last':loss[-1],
              'limitations':'Same synthetic class palette in train and holdout. Does not establish generalization to real satellite imagery. No LoRA run is claimed.'}
    (ROOT/'training/before_after.json').write_text(json.dumps(evidence,indent=2))
    print(json.dumps(evidence,indent=2))
if __name__=='__main__':main()
