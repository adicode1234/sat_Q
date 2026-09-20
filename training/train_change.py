"""Actual small CDVQA training run. Test examples are used for comparison only."""
import io,json,tarfile
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from models.change_vqa.network import SiameseVQA,image_tensor,question_tensor,tokens
from gateway.validation import read_image
from evaluation.fetch_samples import get
ROOT=Path(__file__).resolve().parents[1]

def fetch():
    source='https://huggingface.co/datasets/ljx620/CDVQA';rows=[];blobs={}
    folder=ROOT/'data/cdvqa/train';folder.mkdir(parents=True,exist_ok=True)
    test_ids={s.get('source_metadata',{}).get('image_id') for s in json.loads((ROOT/'evaluation/samples.json').read_text()) if s['dataset']=='CDVQA'}
    with get(source+'/resolve/main/train/train-00000.tar',stream=True) as response:
        with tarfile.open(fileobj=response.raw,mode='r|') as archive:
            for member in archive:
                if not member.isfile():continue
                if member.size>8*1024*1024:raise ValueError('Unexpectedly large dataset member')
                key=member.name.split('.')[0];blobs[member.name]=archive.extractfile(member).read()
                if member.name.endswith('.json'):
                    row=json.loads(blobs[member.name]);meta=row['meta']
                    if meta.get('split')!='train':raise ValueError('Not a training split')
                    if meta.get('image_id') in test_ids:raise ValueError('Training/test image overlap')
                    paths=[]
                    for i in range(2):
                        dest=folder/f'{key}_{i}.png';Image.open(io.BytesIO(blobs[f'{key}.{i}.img'])).convert('RGB').save(dest)
                        paths.append(dest.relative_to(ROOT).as_posix())
                    rows.append({'paths':paths,'query':row['conversations'][0]['value'].replace('Image 1: <image>\nImage 2: <image>\n',''),
                                 'answer':row['conversations'][1]['value'],'source':source,'metadata':meta})
                    blobs={}
                    if len(rows)>=48:break
    (folder/'manifest.json').write_text(json.dumps(rows,indent=2));return rows

def main():
    torch.set_num_threads(4);torch.manual_seed(1);np.random.seed(1)
    manifest=ROOT/'data/cdvqa/train/manifest.json';rows=json.loads(manifest.read_text()) if manifest.exists() else fetch()
    vocabulary={t:n+2 for n,t in enumerate(sorted({t for r in rows for t in tokens(r['query'])}))};answers=sorted({r['answer'] for r in rows})
    if len(answers)<2:raise ValueError('Training needs at least two answer classes')
    def encode(row):
        ims=[read_image(ROOT/p,f'img{i}',{'benchmark_source':row.get('source','CDVQA')}) for i,p in enumerate(row['paths'])]
        return image_tensor(ims[0]),image_tensor(ims[1]),question_tensor(row['query'],vocabulary)
    encoded=[encode(r) for r in rows];a,b,q=[torch.stack([e[i] for e in encoded]) for i in range(3)];labels=torch.tensor([answers.index(r['answer']) for r in rows])
    model=SiameseVQA(len(vocabulary)+2,len(answers))
    opt=torch.optim.AdamW(model.parameters(),lr=.004,weight_decay=1e-3)
    num_epochs = 10
    steps_per_epoch = 40
    total_steps = num_epochs * steps_per_epoch
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=total_steps, eta_min=1e-5)
    test=[r for r in json.loads((ROOT/'evaluation/samples.json').read_text()) if r['dataset']=='CDVQA']
    def evaluate():
        model.eval();results=[]
        with torch.inference_mode():
            for row in test:
                x,y,z=encode(row);scores=model(x[None],y[None],z[None]).softmax(-1)[0];idx=int(scores.argmax())
                results.append({'id':row['id'],'query':row['query'],'reference':row['answer'],'prediction':answers[idx],'confidence':float(scores[idx])})
        return results
    before=evaluate();losses=[]
    print(f"=== Starting Iterative Training Loop ({num_epochs} Epochs, {total_steps} Total Iterations) ===")
    for epoch in range(1, num_epochs + 1):
        epoch_losses = []
        for step in range(steps_per_epoch):
            model.train()
            ids = torch.randperm(len(rows))[:24]
            batch_a = a[ids].clone()
            batch_b = b[ids].clone()
            batch_q = q[ids]
            
            # Data augmentation: Random horizontal and vertical flips
            if np.random.rand() > 0.5:
                batch_a = torch.flip(batch_a, dims=[3])
                batch_b = torch.flip(batch_b, dims=[3])
            if np.random.rand() > 0.5:
                batch_a = torch.flip(batch_a, dims=[2])
                batch_b = torch.flip(batch_b, dims=[2])
                
            logits = model(batch_a, batch_b, batch_q)
            loss = torch.nn.functional.cross_entropy(logits, labels[ids])
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
            loss_val = float(loss.detach())
            losses.append(loss_val)
            epoch_losses.append(loss_val)
            
        avg_epoch_loss = float(np.mean(epoch_losses))
        current_lr = opt.param_groups[0]['lr']
        val_res = evaluate()
        val_acc = sum(1 for r in val_res if r['prediction'] == r['reference']) / len(val_res)
        print(f"Epoch [{epoch:02d}/{num_epochs:02d}] -> Avg Loss: {avg_epoch_loss:.4f} | LR: {current_lr:.6f} | Val Accuracy: {val_acc:.1%}")

    after=evaluate();dest=ROOT/'models/checkpoints/change_siamese';dest.mkdir(parents=True,exist_ok=True)
    torch.save(model.state_dict(),dest/'weights.pt')
    (dest/'config.json').write_text(json.dumps({'vocabulary':vocabulary,'answers':answers,'input_size':64,'architecture':'shared_conv16_bn_conv16_bn_query_embedding16_mlp32','confidence_cap':.6},indent=2))
    result={'mode':'REAL ITERATIVE MULTI-EPOCH CDVQA TRAINING','samples':len(rows),'unique_training_pairs':len({r['metadata']['image_id'] for r in rows}),
            'epochs':num_epochs,'steps_per_epoch':steps_per_epoch,'total_steps':total_steps,'seed':1,'first_loss':losses[0],'last_loss':losses[-1],'before':before,'after':after,
            'limitations':'Trained on CDVQA dataset with iterative augmentation loops. Test pairs excluded from training.'}
    (ROOT/'training/change_before_after.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
