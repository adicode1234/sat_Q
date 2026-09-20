"""Small cross-attention segmenter; weights trained on disclosed synthetic pairs."""
import torch
from torch import nn
import numpy as np
from gateway.validation import rgb


class CrossModalNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.optical=nn.Conv2d(3,24,4,4)
        self.sar=nn.Conv2d(1,24,4,4)
        self.position=nn.Parameter(torch.randn(1,256,24)*.01)
        self.attention=nn.MultiheadAttention(24,3,batch_first=True)
        self.head=nn.Sequential(nn.Linear(72,48),nn.GELU(),nn.Linear(48,4))

    def forward(self,optical,sar):
        a=self.optical(optical).flatten(2).transpose(1,2)
        b=self.sar(sar).flatten(2).transpose(1,2)
        mixed,_=self.attention(a+self.position,b+self.position,b,need_weights=False)
        return self.head(torch.cat([a,b,mixed],-1)).transpose(1,2).reshape(-1,4,16,16)


def tensors(optical,sar):
    from PIL import Image
    a=np.asarray(Image.fromarray(rgb(optical)).resize((64,64)),dtype='float32')/255
    v=sar['array'][0].copy()
    if sar['sar_units']=='linear':v=10*np.log10(np.where(v>0,v,np.nan))
    v=np.clip((np.nan_to_num(v,nan=-12)+30)/30,0,1)
    b=np.asarray(Image.fromarray(v).resize((64,64)),dtype='float32')
    return torch.from_numpy(a.transpose(2,0,1).copy())[None],torch.from_numpy(b.copy())[None,None]
