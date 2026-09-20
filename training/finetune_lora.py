"""Optional real ViLT LoRA training on a user-prepared remote-sensing JSONL.
Run: python -m training.finetune_lora --manifest data/train.jsonl --steps 20
Each row: {"image":"path", "question":"...", "answer":"...", "split":"train"}.
Requires torch, transformers, peft; CPU works slowly. No test split is accepted.
"""
import argparse,json
from pathlib import Path
def main():
    import torch
    from PIL import Image
    from transformers import ViltProcessor,ViltForQuestionAnswering
    from peft import LoraConfig,get_peft_model
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--steps',type=int,default=20);args=p.parse_args()
    torch.set_num_threads(4);torch.manual_seed(42)
    root=Path(__file__).resolve().parents[1];base=root/'models/checkpoints/vilt'
    processor=ViltProcessor.from_pretrained(base,local_files_only=True)
    model=ViltForQuestionAnswering.from_pretrained(base,local_files_only=True)
    model=get_peft_model(model,LoraConfig(r=4,lora_alpha=8,target_modules=['query','value'],lora_dropout=.05,bias='none'))
    rows=[json.loads(l) for l in Path(args.manifest).read_text().splitlines() if l.strip()]
    if not rows or any(r.get('split')!='train' for r in rows):raise ValueError('Only explicitly labeled training samples are accepted')
    for row in rows:row['image']=str(root/row['image'])
    def predict(row):
        model.eval()
        with torch.inference_mode():
            inputs=processor(Image.open(row['image']).convert('RGB'),row['question'],return_tensors='pt')
            scores=model(**inputs).logits.sigmoid()[0];idx=int(scores.argmax())
        return {'answer':model.config.id2label[idx],'score':float(scores[idx])}
    heldout=json.loads((root/'evaluation/samples.json').read_text())[0]
    comparison_row={'image':str(root/heldout['paths'][0]),'question':heldout['query']}
    before=predict(comparison_row)
    opt=torch.optim.AdamW([v for v in model.parameters() if v.requires_grad],lr=2e-4)
    model.train();losses=[]
    for step in range(args.steps):
        row=rows[step%len(rows)];answer=str(row['answer']).lower();label=model.config.label2id.get(answer)
        if label is None:raise ValueError(f'Answer outside ViLT vocabulary: {answer}')
        inputs=processor(Image.open(row['image']).convert('RGB'),row['question'],return_tensors='pt')
        targets=torch.zeros(1,model.config.num_labels);targets[0,label]=1
        loss=model(**inputs,labels=targets).loss;loss.backward();opt.step();opt.zero_grad();losses.append(float(loss.detach()));print(step,losses[-1],flush=True)
    dest=root/'models/checkpoints/vilt_lora';model.save_pretrained(dest)
    after=predict(comparison_row)
    record={'steps':args.steps,'losses':losses,'manifest':args.manifest,'training_rows_available':len(rows),
            'training_rows_used':min(args.steps,len(rows)),'source':'VRSBench official train annotations and images',
            'method':'ViLT query/value attention LoRA, rank 4, alpha 8, seed 42, AdamW 0.0002',
            'trainable_parameters':sum(v.numel() for v in model.parameters() if v.requires_grad),
            'comparison':{**comparison_row,'reference':heldout['answer'],'split':heldout['split'],'before':before,'after':after},
            'limitations':'Small CPU adaptation run demonstrates real weight updates, not benchmark-quality generalization. The held-out example is not used for training.'}
    (root/'training/lora_run.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))
if __name__=='__main__':main()
