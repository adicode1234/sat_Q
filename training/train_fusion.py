"""CPU cross-attention training on SYNTHETIC data, never a real-data accuracy claim."""
import json
from pathlib import Path
import numpy as np
import torch
from models.fusion_optical_sar.network import CrossModalNet,tensors
from training.make_demo import scene
ROOT=Path(__file__).resolve().parents[1]


def samples(seeds):
    aa=[];bb=[];yy=[]
    for seed in seeds:
        rng=np.random.default_rng(seed)
        # Apply the same independently sampled spatial transform to both modalities.
        a,y=scene(seed,64);shift=int(rng.integers(0,64));a=np.roll(a,shift,2);y=np.roll(y,shift,1)
        turns=int(rng.integers(0,4));a=np.rot90(a,turns,(1,2)).copy();y=np.rot90(y,turns).copy()
        a[:3]=np.clip(a[:3]*rng.uniform(.8,1.2,(3,1,1)),0,1)
        sar=np.array([-22,-11,-6,-15])[y]+rng.normal(0,2,y.shape)
        if seed%2:
            a[:3,8:28,16:48]=rng.uniform(.8,1)
        optical={'array':a,'bands':['red','green','blue','nir','swir']}
        radar={'array':sar[None],'sar_units':'db'}
        x,b=tensors(optical,radar);aa.append(x);bb.append(b)
        yy.append(torch.from_numpy(y[2::4,2::4].copy()).long())
    return torch.cat(aa),torch.cat(bb),torch.stack(yy)


def main():
    torch.set_num_threads(4);torch.manual_seed(87)
    model=CrossModalNet();train=samples(range(1000,1128));test=samples(range(2000,2032))
    def score():
        model.eval()
        with torch.inference_mode():
            pred=model(*test[:2]).argmax(1)
            return float((pred==test[2]).float().mean())
    before=score();optimizer=torch.optim.AdamW(model.parameters(),lr=.003,weight_decay=1e-4)
    sched=torch.optim.lr_scheduler.CosineAnnealingLR(optimizer,T_max=300)
    for step in range(300):
        model.train();ids=torch.randperm(128)[:16];optimizer.zero_grad()
        loss=torch.nn.functional.cross_entropy(model(train[0][ids],train[1][ids]),train[2][ids]);loss.backward();optimizer.step()
        sched.step()
        if step%60==0:print('step',step,'loss',float(loss.detach()),flush=True)
    after=score();folder=ROOT/'models/checkpoints/fusion_cross_attention';folder.mkdir(parents=True,exist_ok=True)
    torch.save(model.state_dict(),folder/'weights.pt')
    evidence={'scope':'SYNTHETIC ONLY; shared palette and simulated SAR; no real-world generalization established',
              'architecture':'optical and SAR patch encoders + 3-head cross-attention + dense classification head',
              'train_scenes':128,'holdout_scenes':32,'steps':300,'seed':87,'before_pixel_accuracy':before,'after_pixel_accuracy':after,
              'train_seed_range':[1000,1127],'holdout_seed_range':[2000,2031],
              'limitations':['Synthetic SAR class distributions are simplified.','Clouds are rectangular synthetic perturbations.','Output is 16x16 patch classification, not validated pixel segmentation.']}
    (folder/'config.json').write_text(json.dumps(evidence,indent=2));(ROOT/'training/fusion_before_after.json').write_text(json.dumps(evidence,indent=2));print(json.dumps(evidence,indent=2))
if __name__=='__main__':main()
