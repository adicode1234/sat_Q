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

    with np.load(ROOT/'models/checkpoints/rgb_water_real.npz') as f:w={k:f[k].copy() for k in f.files}
    mean=w['mean'];std=w['std']
    tx=torch.from_numpy((data['train'][0]-mean)/std);ty=torch.from_numpy(data['train'][1])
    model=nn.Sequential(nn.Linear(tx.shape[1],64),nn.ReLU(),nn.Linear(64,2))
    with torch.no_grad():
        model[0].weight.copy_(torch.from_numpy(w['w1'].T));model[0].bias.copy_(torch.from_numpy(w['b1']))
        model[2].weight.copy_(torch.from_numpy(w['w2'].T));model[2].bias.copy_(torch.from_numpy(w['b2']))
    def logits(split):
        with torch.inference_mode():return model(torch.from_numpy((data[split][0]-mean)/std)).numpy()
    initial=copy.deepcopy(model.state_dict());best=initial;best_t=float(w['temperature']);best_th=float(w['threshold'])
    baseline=metrics(logits('validation'),data['validation'][1],best_t,best_th);selected=baseline;history=[]
    for lr in (.0001,.0003,.001):
        torch.manual_seed(2027);model.load_state_dict(initial)
        opt=torch.optim.AdamW(model.parameters(),lr=lr,weight_decay=.002)
        scheduler=torch.optim.lr_scheduler.CosineAnnealingLR(opt,T_max=600)
        for step in range(1,601):
            ids=torch.randint(len(ty),(2048,));opt.zero_grad();loss=nn.functional.cross_entropy(model(tx[ids]),ty[ids]);loss.backward();opt.step();scheduler.step()
            if step%200==0:
                v=logits('validation');vy=torch.from_numpy(data['validation'][1])
                t=float(min(np.linspace(.7,1.5,9),key=lambda x:float(nn.functional.cross_entropy(torch.from_numpy(v)/x,vy))))
                th=float(max(np.linspace(.2,.7,21),key=lambda x:metrics(v,data['validation'][1],t,x)['iou']))
                score=metrics(v,data['validation'][1],t,th)
                promote=score['iou']>selected['iou'] and score['brier']<=baseline['brier']+.001
                history.append({'learning_rate':lr,'step':step,'validation':score,'selected':promote})
                if promote:best=copy.deepcopy(model.state_dict());selected=score;best_t=t;best_th=th
                print(lr,step,score['iou'],promote,flush=True)
    model.load_state_dict(best)
    promoted=selected['iou']>baseline['iou']
    result={'baseline_validation':baseline,'selected_validation':selected,'test':metrics(logits('test'),data['test'][1],best_t,best_th),'promoted':promoted,'steps':1800,'history':history,'scope':'Same fixed Sen1Floods11 chip splits and sampled RGB pixels. Validation selects all weights and calibration; test evaluated only after selection. Previously inspected test set is not a fresh benchmark. Screenshot transfer remains unvalidated.'}
    if promoted:
        np.savez(ROOT/'models/checkpoints/rgb_water_real.npz',mean=mean,std=std,w1=model[0].weight.detach().numpy().T,b1=model[0].bias.detach().numpy(),w2=model[2].weight.detach().numpy().T,b2=model[2].bias.detach().numpy(),temperature=best_t,threshold=best_th)
    (ROOT/'training/offline_rgb_refinement_results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
if __name__=='__main__':main()
