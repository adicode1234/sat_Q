"""Supervised RGB water training; fixed chip splits, validation-selected weights."""
import copy,json
import numpy as np
import torch,rasterio
from torch import nn
from gateway.validation import read_image
from models.rgb_water import pixels
from models.rgb_water_expert import features,ROOT
from training.train_water import metrics

def main():
    torch.set_num_threads(4);torch.manual_seed(2026);rng=np.random.default_rng(2026)
    rows=json.loads((ROOT/'data/sen1floods11/manifest.json').read_text());data={}
    for split in ('train','validation','test'):
        xs=[];ys=[];old=[]
        for row in rows:
            if row['split']!=split:continue
            image=read_image(ROOT/row['s2'],'img1',row['options'][0]);rgb,valid=pixels(image)
            with rasterio.open(ROOT/row['label']) as f:y=f.read(1)
            valid &= (y==0)|(y==1);x=features(rgb)[valid];y=y[valid]
            ids=rng.choice(len(y),min(5000,len(y)),replace=False);xs.append(x[ids]);ys.append(y[ids])
            # Reproduce deployed RGB colour rules on its original reflectance scale.
            a=image['array'][[image['bands'].index(b) for b in ('red','green','blue')]].transpose(1,2,0)
            r,g,b=np.moveaxis(a,-1,0)
            w=(((b>r*1.15)&(g>r*1.05)&(r<.42))|((r<.35)&(g<.45)&(b<.5)&(b>=r)&(g>=r))|((b>.28)&(b>r+.02)&(g>r+.01)&(r<.44)))&~((g>r*1.15)&(g>b*1.08))
            old.append(w[valid][ids])
        data[split]=(np.concatenate(xs),np.concatenate(ys).astype('int64'),np.concatenate(old))
        print('loaded',split,len(data[split][1]),flush=True)
    mean=data['train'][0].mean(0);std=np.maximum(data['train'][0].std(0),1e-4)
    tx=torch.from_numpy((data['train'][0]-mean)/std);ty=torch.from_numpy(data['train'][1])
    model=nn.Sequential(nn.Linear(tx.shape[1],64),nn.ReLU(),nn.Linear(64,2));opt=torch.optim.AdamW(model.parameters(),lr=.003,weight_decay=.001)
    schedule=torch.optim.lr_scheduler.CosineAnnealingLR(opt,T_max=1600)
    def logits(split):
        with torch.inference_mode():return model(torch.from_numpy((data[split][0]-mean)/std)).numpy()
    best=None;best_loss=float('inf');best_step=0
    for step in range(1,1601):
        ids=torch.randint(len(ty),(2048,));opt.zero_grad();loss=nn.functional.cross_entropy(model(tx[ids]),ty[ids]);loss.backward();opt.step();schedule.step()
        if step%200==0:
            val_loss=float(nn.functional.cross_entropy(torch.from_numpy(logits('validation')),torch.from_numpy(data['validation'][1])))
            if val_loss<best_loss:best_loss=val_loss;best=copy.deepcopy(model.state_dict());best_step=step
            print(step,val_loss,flush=True)
    model.load_state_dict(best);v=logits('validation');vy=torch.from_numpy(data['validation'][1])
    temperature=float(min(np.linspace(.5,2,31),key=lambda t:float(nn.functional.cross_entropy(torch.from_numpy(v)/t,vy))))
    threshold=float(max(np.linspace(.1,.9,33),key=lambda t:metrics(v,data['validation'][1],temperature,t)['iou']))
    results={s:metrics(logits(s),data[s][1],temperature,threshold) for s in ('validation','test')}
    np.savez(ROOT/'models/checkpoints/rgb_water_real.npz',mean=mean,std=std,w1=model[0].weight.detach().numpy().T,b1=model[0].bias.detach().numpy(),w2=model[2].weight.detach().numpy().T,b2=model[2].bias.detach().numpy(),temperature=temperature,threshold=threshold)
    results.update(steps=1600,selected_step=best_step,train_chips=96,validation_chips=24,test_chips=24,temperature=temperature,threshold=threshold,scope='Sen1Floods11 fixed RGB rendering at reflectance / 0.3; sampled 5000 valid pixels/chip. Transfer to user JPEGs and other sensors is unvalidated. Spatial context uses 5x5 RGB moments. No test-label training or checkpoint selection.')
    (ROOT/'training/rgb_water_training_results.json').write_text(json.dumps(results,indent=2));print(json.dumps(results),flush=True)
if __name__=='__main__':main()
