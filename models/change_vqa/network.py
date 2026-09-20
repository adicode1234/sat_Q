"""Small shared-weight Siamese encoder with query conditioning; CPU research model."""
import re
import numpy as np
from PIL import Image
import torch
from torch import nn
from gateway.validation import rgb

def tokens(query):return re.findall(r'[a-z0-9]+',query.lower())

class SiameseVQA(nn.Module):
    def __init__(self,vocab_size,answers):
        super().__init__()
        self.encoder=nn.Sequential(
            nn.Conv2d(3,16,3,padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16,16,3,padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d(1)
        )
        self.words=nn.Embedding(vocab_size,16,padding_idx=0)
        self.head=nn.Sequential(nn.Linear(64,32),nn.ReLU(),nn.Linear(32,answers))
    def forward(self,before,after,query):
        a=self.encoder(before).flatten(1);b=self.encoder(after).flatten(1)
        mask=(query!=0).unsqueeze(-1);q=(self.words(query)*mask).sum(1)/mask.sum(1).clamp(min=1)
        return self.head(torch.cat([a,b,torch.abs(b-a),q],dim=1))

def image_tensor(image):
    arr=np.array(Image.fromarray(rgb(image)).resize((64,64)),dtype=np.float32)/255
    return torch.from_numpy(arr.transpose(2,0,1).copy())

def question_tensor(query,vocabulary):
    ids=[vocabulary.get(t,1) for t in tokens(query)][:48]
    return torch.tensor(ids+[0]*(48-len(ids)),dtype=torch.long)
