"""Candidate LoRA refinement with image-disjoint validation and promotion gate."""
import copy,json
from pathlib import Path
import torch
from PIL import Image
from transformers import ViltProcessor,ViltForQuestionAnswering
from peft import PeftModel
ROOT=Path(__file__).resolve().parents[1]
def main():
    torch.set_num_threads(4);torch.manual_seed(2026)
    rows=[json.loads(s) for s in (ROOT/'data/vrsbench/train.jsonl').read_text().splitlines() if s.strip()]
    assert all(r['split']=='train' for r in rows)
    images=sorted({r['image'] for r in rows});val_images=set(images[-2:])
    train=[r for r in rows if r['image'] not in val_images];val=[r for r in rows if r['image'] in val_images]
    base=ROOT/'models/checkpoints/vilt';dest=ROOT/'models/checkpoints/vilt_lora'
    model=PeftModel.from_pretrained(ViltForQuestionAnswering.from_pretrained(base,local_files_only=True),dest,is_trainable=True,local_files_only=True)
    processor=ViltProcessor.from_pretrained(base,local_files_only=True)
    def encode(r):return processor(Image.open(ROOT/r['image']).convert('RGB'),r['question'],return_tensors='pt')
    cached=[(encode(r),model.config.label2id[r['answer'].lower()]) for r in train]
    def score():
        model.eval();correct=0;loss=0
        with torch.inference_mode():
            for r in val:
                logits=model(**encode(r)).logits
                label=model.config.label2id[r['answer'].lower()];correct+=int(int(logits.argmax())==label)
                loss+=float(torch.nn.functional.cross_entropy(logits,torch.tensor([label])))
        return {'accuracy':correct/len(val),'nll':loss/len(val),'questions':len(val)}
    before=score();best_score=before;best=None;opt=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=5e-5,weight_decay=.01)
    for step in range(1,65):
        model.train();inputs,label=cached[int(torch.randint(len(cached),(1,)))];target=torch.zeros(1,model.config.num_labels);target[0,label]=1
        opt.zero_grad();loss=model(**inputs,labels=target).loss;loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1);opt.step()
        if step%16==0:
            result=score();print(step,result,flush=True)
            if result['accuracy']>best_score['accuracy'] or (result['accuracy']==best_score['accuracy'] and result['nll']<best_score['nll']):
                best_score=result;best={k:v.detach().clone() for k,v in model.named_parameters() if v.requires_grad}
    # Original adapter has seen these images, so validation is continuation-only.
    # Require both better validation accuracy and NLL; do not claim independent generalization.
    promote=best is not None and best_score['accuracy']>before['accuracy'] and best_score['nll']<before['nll']
    if promote:
        with torch.no_grad():
            for k,p in model.named_parameters():
                if k in best:p.copy_(best[k])
        model.save_pretrained(dest)
    record={'before':before,'candidate':best_score,'promoted':promote,'steps':64,'train_images':len(images)-len(val_images),'validation_images':len(val_images),'limitations':'Only 16 questions / 6 images available. Validation images excluded from this refinement but present in historical adapter training; this is not independent accuracy evidence. Public test images never train or select weights.'}
    (ROOT/'training/vqa_refinement_results.json').write_text(json.dumps(record,indent=2));print(record,flush=True)
if __name__=='__main__':main()
