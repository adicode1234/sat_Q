"""Spatial segmentation trained only on official training chips, selected on validation."""
import copy,json,time
from pathlib import Path
import numpy as np,rasterio,torch
from torch import nn
from gateway.validation import read_image
from models.rgb_water import pixels
from models.context_water import ContextWater,ROOT
from evaluation.evaluate_rgb_water import metrics

def main():
    torch.set_num_threads(4);torch.manual_seed(9026);np.random.seed(9026)
    rows=json.loads((ROOT/'data/sen1floods11/manifest.json').read_text());data={}
    for split in ('train','validation','test'):
        xx=[];yy=[]
        for row in [r for r in rows if r['split']==split]:
            image=read_image(ROOT/row['s2'],'img1',row['options'][0]);a,v=pixels(image)
            with rasterio.open(ROOT/row['label']) as f:y=f.read(1)
            y=np.where(v&((y==0)|(y==1)),y,255)
            x=torch.from_numpy((a/255).transpose(2,0,1).copy())[None]
            xx.append(nn.functional.interpolate(x,size=(128,128),mode='bilinear',align_corners=False)[0])
            yy.append(nn.functional.interpolate(torch.from_numpy(y.astype('float32'))[None,None],size=(128,128),mode='nearest')[0,0].long())
        data[split]=(torch.stack(xx),torch.stack(yy));print('loaded',split,len(xx),flush=True)
    model=ContextWater();opt=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.01)
    best=None;best_iou=-1;best_epoch=0;best_threshold=.5;history=[]
    def predictions(split):
        model.eval();out=[]
        with torch.inference_mode():
            for x,y in zip(*data[split]):
                p=model(x[None]).softmax(1)[0,1].numpy();valid=y.numpy()!=255;out.append((p[valid],y.numpy()[valid]))
        return out
    for epoch in range(1,21):
        model.train();losses=[];order=torch.randperm(len(data['train'][0]))
        for ids in order.split(4):
            x=data['train'][0][ids].clone();y=data['train'][1][ids].clone()
            if torch.rand(())>.5:x=x.flip(-1);y=y.flip(-1)
            if torch.rand(())>.5:x=x.flip(-2);y=y.flip(-2)
            x=(x*(.8+.4*torch.rand(len(ids),1,1,1))).clamp(0,1)
            logits=model(x);valid=y!=255
            if not valid.any():continue
            ce=nn.functional.cross_entropy(logits,y,ignore_index=255)
            p=logits.softmax(1)[:,1];target=(y==1).float();dice=1-(2*(p*target*valid).sum()+1)/((p*valid).sum()+(target*valid).sum()+1)
            loss=ce+.3*dice;opt.zero_grad();loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1);opt.step();losses.append(float(loss.detach()))
        val=predictions('validation');threshold=float(max(np.linspace(.2,.8,13),key=lambda t:metrics(val,t)['iou']));score=metrics(val,threshold)
        if score['iou']>best_iou:best_iou=score['iou'];best=copy.deepcopy(model.state_dict());best_epoch=epoch;best_threshold=threshold
        history.append({'epoch':epoch,'loss':float(np.mean(losses)),'validation_iou':score['iou']});print(history[-1],flush=True)
    model.load_state_dict(best);validation=metrics(predictions('validation'),best_threshold);test=metrics(predictions('test'),best_threshold)
    record={'validation':validation,'test':test,'epochs':20,'selected_epoch':best_epoch,'threshold':best_threshold,'chip_splits':{s:len(data[s][0]) for s in data},'history':history,'scope':'128x128 labelled chip segmentation; fixed official Sen1Floods11 splits. Test evaluated only after validation checkpoint selection. Not directly comparable to previous sampled full-resolution pixel protocol; sensor/screenshot transfer unvalidated.'}
    torch.save({'state':model.state_dict(),'threshold':best_threshold,'validation_iou':validation['iou']},ROOT/'models/checkpoints/context_water.pt')
    (ROOT/'training/context_water_results.json').write_text(json.dumps(record,indent=2));print(json.dumps(record),flush=True)
if __name__=='__main__':main()
