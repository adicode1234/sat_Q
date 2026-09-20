"""Train real optical/SAR/joint water MLPs. Calibration uses validation only."""
import json
from pathlib import Path
import numpy as np
import rasterio
import torch
from torch import nn
from gateway.validation import read_image
from models.water import inputs
ROOT=Path(__file__).resolve().parents[1]

def rows(samples,kind,limit):
    xs=[];ys=[];rng=np.random.default_rng(731)
    for row in samples:
        optical=read_image(ROOT/row['s2'],'img1',row['options'][0]);sar=read_image(ROOT/row['s1'],'img2',row['options'][1])
        x,valid,_=inputs([optical,sar],kind)
        with rasterio.open(ROOT/row['label']) as src:
            y=src.read(1);assert y.shape==valid.shape
            assert src.crs==rasterio.crs.CRS.from_string(sar['crs'])
            assert np.allclose(list(src.transform)[:6],sar['transform'])
        valid &= (y==0)|(y==1);x=x[valid];y=y[valid]
        ids=rng.choice(len(y),min(limit,len(y)),replace=False)
        xs.append(x[ids]);ys.append(y[ids])
    return np.concatenate(xs),np.concatenate(ys).astype('int64')

def metrics(logits,y,t=1,threshold=.5):
    p=torch.softmax(torch.from_numpy(logits)/t,dim=1).numpy()[:,1];pred=p>=threshold
    tp=int(((y==1)&pred).sum());fp=int(((y==0)&pred).sum());fn=int(((y==1)&~pred).sum())
    ece=0
    for low in np.linspace(0,.9,10):
        selected=(p>=low)&(p<low+.1 if low<.9 else p<=1)
        if selected.any():ece+=selected.mean()*abs(p[selected].mean()-y[selected].mean())
    return {'iou':tp/max(tp+fp+fn,1),'precision':tp/max(tp+fp,1),'recall':tp/max(tp+fn,1),
            'f1':2*tp/max(2*tp+fp+fn,1),'brier':float(np.mean((p-y)**2)),'ece_10_bins':float(ece),
            'pixels':len(y),'tp':tp,'fp':fp,'fn':fn}

def main():
    torch.set_num_threads(4);np.random.seed(731);torch.manual_seed(731)
    samples=json.loads((ROOT/'data/sen1floods11/manifest.json').read_text());result={}
    folder=ROOT/'models/checkpoints/water_real';folder.mkdir(parents=True,exist_ok=True)
    for kind in ('sar','optical','joint'):
        data={s:rows([r for r in samples if r['split']==s],kind,10000 if s=='train' else 20000) for s in ('train','validation','test')}
        x,y=data['train'];mean=x.mean(0);std=np.maximum(x.std(0),1e-4)
        model=nn.Sequential(nn.Linear(x.shape[1],64),nn.ReLU(),nn.Linear(64,2))
        tx=torch.from_numpy((x-mean)/std);ty=torch.from_numpy(y);optimizer=torch.optim.AdamW(model.parameters(),lr=.004,weight_decay=1e-4)
        sched=torch.optim.lr_scheduler.CosineAnnealingLR(optimizer,T_max=1600)
        def logits(split):
            with torch.inference_mode():return model(torch.from_numpy((data[split][0]-mean)/std)).numpy()
        before=metrics(logits('test'),data['test'][1])
        for step in range(1600):
            ids=torch.randint(len(ty),(4096,));optimizer.zero_grad();loss=nn.functional.cross_entropy(model(tx[ids]),ty[ids]);loss.backward();optimizer.step()
            sched.step()
        val=logits('validation');vy=torch.from_numpy(data['validation'][1])
        temps=np.linspace(.5,3,51);nll=[float(nn.functional.cross_entropy(torch.from_numpy(val)/t,vy)) for t in temps];temp=float(temps[int(np.argmin(nll))])
        thresholds=np.linspace(.1,.9,33);threshold=float(max(thresholds,key=lambda th:metrics(val,data['validation'][1],temp,th)['iou']))
        weights={'mean':mean,'std':std,'w1':model[0].weight.detach().numpy().T,'b1':model[0].bias.detach().numpy(),
                 'w2':model[2].weight.detach().numpy().T,'b2':model[2].bias.detach().numpy(),'temperature':temp}
        np.savez(folder/f'{kind}.npz',**weights)
        result[kind]={'temperature':temp,'threshold':threshold,'test':metrics(logits('test'),data['test'][1],temp,threshold),
                      'validation_uncalibrated':metrics(val,data['validation'][1]),'validation_calibrated':metrics(val,data['validation'][1],temp,threshold),
                      'before_test':before,'steps':1600,'seed':731,'split_chips':{s:len([r for r in samples if r['split']==s]) for s in data},
                      'scope':'Original Sen1Floods11 official chip splits; 10k train / 20k evaluation valid pixels per chip, sampled without replacement. Events can overlap between splits; no cross-sensor generalization claim.'}
        print(kind,json.dumps(result[kind]['test']),flush=True)
    (folder/'evaluation.json').write_text(json.dumps(result,indent=2));(ROOT/'training/water_before_after.json').write_text(json.dumps(result,indent=2))
if __name__=='__main__':main()
