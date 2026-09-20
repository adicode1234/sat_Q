"""Warm-start real water experts; select weights on validation, then test once."""
import copy, json
from pathlib import Path
import numpy as np
import torch
from torch import nn
from training.train_water import rows, metrics, ROOT

def main():
    torch.set_num_threads(4)
    samples=json.loads((ROOT/'data/sen1floods11/manifest.json').read_text())
    folder=ROOT/'models/checkpoints/water_real'
    evaluation=json.loads((folder/'evaluation.json').read_text())
    results={}
    for kind in ('sar','optical','joint'):
        torch.manual_seed(2026)
        data={s:rows([r for r in samples if r['split']==s],kind,10000 if s=='train' else 20000) for s in ('train','validation','test')}
        with np.load(folder/f'{kind}.npz') as f:w={k:f[k].copy() for k in f.files}
        model=nn.Sequential(nn.Linear(len(w['mean']),64),nn.ReLU(),nn.Linear(64,2))
        with torch.no_grad():
            for layer,weight,bias in ((0,'w1','b1'),(2,'w2','b2')):
                model[layer].weight.copy_(torch.from_numpy(w[weight].T));model[layer].bias.copy_(torch.from_numpy(w[bias]))
        data={s:(torch.from_numpy((x-w['mean'])/w['std']),y) for s,(x,y) in data.items()}
        def logits(split):
            model.eval()
            with torch.inference_mode():return torch.cat([model(chunk) for chunk in data[split][0].split(65536)]).numpy()
        old=evaluation[kind];old_val=metrics(logits('validation'),data['validation'][1],float(w['temperature']),old['threshold'])
        before=metrics(logits('test'),data['test'][1],float(w['temperature']),old['threshold'])
        best=copy.deepcopy(model.state_dict());best_nll=float(nn.functional.cross_entropy(torch.from_numpy(logits('validation')),torch.from_numpy(data['validation'][1])))
        opt=torch.optim.AdamW(model.parameters(),lr=.0005,weight_decay=.001)
        sched=torch.optim.lr_scheduler.CosineAnnealingLR(opt,T_max=1200)
        y=torch.from_numpy(data['train'][1]);best_step=0
        for step in range(1,1201):
            model.train();ids=torch.randint(len(y),(4096,));opt.zero_grad()
            loss=nn.functional.cross_entropy(model(data['train'][0][ids]),y[ids]);loss.backward();opt.step();sched.step()
            if step%200==0:
                nll=float(nn.functional.cross_entropy(torch.from_numpy(logits('validation')),torch.from_numpy(data['validation'][1])))
                if nll<best_nll:best_nll=nll;best=copy.deepcopy(model.state_dict());best_step=step
                print(kind,step,'validation_nll',round(nll,5),flush=True)
        model.load_state_dict(best);val=logits('validation');vy=torch.from_numpy(data['validation'][1])
        temperatures=np.linspace(.5,2,31)
        t=float(min(temperatures,key=lambda t:float(nn.functional.cross_entropy(torch.from_numpy(val)/t,vy))))
        threshold=float(max(np.linspace(.1,.9,33),key=lambda th:metrics(val,data['validation'][1],t,th)['iou']))
        selected=metrics(val,data['validation'][1],t,threshold)
        promote=selected['iou']>old_val['iou'] and selected['brier']<=old_val['brier']+.001
        after=metrics(logits('test'),data['test'][1],t,threshold)
        results[kind]={'baseline_validation':old_val,'candidate_validation':selected,'baseline_test':before,'candidate_test':after,'promoted':promote,'selected_step':best_step,'extra_steps':1200,'selection':'Validation IoU improves and Brier degrades by at most 0.001. Test never selects weights.'}
        if promote:
            np.savez(folder/f'{kind}.npz',mean=w['mean'],std=w['std'],w1=model[0].weight.detach().numpy().T,b1=model[0].bias.detach().numpy(),w2=model[2].weight.detach().numpy().T,b2=model[2].bias.detach().numpy(),temperature=t)
            evaluation[kind]={**old,'temperature':t,'threshold':threshold,'test':after,'validation_calibrated':selected,'refinement':results[kind]}
        print(kind,json.dumps(results[kind]),flush=True)
        (ROOT/'training/offline_refinement_results.json').write_text(json.dumps(results,indent=2))
    (folder/'evaluation.json').write_text(json.dumps(evaluation,indent=2))
if __name__=='__main__':main()
