"""Small spatial RGB water segmenter; validation-selected, sensor transfer uncalibrated."""
from pathlib import Path
from functools import lru_cache
import numpy as np
import torch
from torch import nn
ROOT=Path(__file__).resolve().parents[1]
class ContextWater(nn.Module):
    def __init__(self):
        super().__init__()
        def block(a,b):return nn.Sequential(nn.Conv2d(a,b,3,padding=1),nn.GroupNorm(4,b),nn.ReLU(),nn.Conv2d(b,b,3,padding=1),nn.GroupNorm(4,b),nn.ReLU())
        self.a=block(3,16);self.b=block(16,32);self.c=block(32,64);self.d=block(96,32);self.e=block(48,16);self.head=nn.Conv2d(16,2,1)
    def forward(self,x):
        a=self.a(x);b=self.b(nn.functional.avg_pool2d(a,2));c=self.c(nn.functional.avg_pool2d(b,2))
        d=self.d(torch.cat([nn.functional.interpolate(c,size=b.shape[-2:],mode='bilinear',align_corners=False),b],1))
        e=self.e(torch.cat([nn.functional.interpolate(d,size=a.shape[-2:],mode='bilinear',align_corners=False),a],1))
        return self.head(e)
@lru_cache(maxsize=1)
def load():
    checkpoint=torch.load(ROOT/'models/checkpoints/context_water.pt',map_location='cpu',weights_only=True)
    model=ContextWater();model.load_state_dict(checkpoint['state']);return model.eval(),checkpoint

def predict(rgb,valid):
    model,checkpoint=load();h,w=valid.shape
    x=torch.from_numpy((rgb/255).transpose(2,0,1).copy())[None]
    # Whole-scene structure survives resizing; training uses 128x128 chip context.
    with torch.inference_mode():
        logits=model(nn.functional.interpolate(x,size=(128,128),mode='bilinear',align_corners=False))
        p=nn.functional.interpolate(logits,size=(h,w),mode='bilinear',align_corners=False).softmax(1)[0,1].numpy()
    p[~valid]=np.nan
    return p,float(checkpoint['threshold'])
