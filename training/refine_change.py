"""Bounded change-VQA refinement; image-pair split and explicit data sufficiency gate."""
import json
import torch
from pathlib import Path
from models.change_vqa.network import SiameseVQA,image_tensor,question_tensor
from gateway.validation import read_image
ROOT=Path(__file__).resolve().parents[1]
def main():
    torch.set_num_threads(4);torch.manual_seed(2026)
    rows=json.loads((ROOT/'data/cdvqa/train/manifest.json').read_text());groups=sorted({r['metadata']['image_id'] for r in rows})
    folder=ROOT/'models/checkpoints/change_siamese';config=json.loads((folder/'config.json').read_text());vocab=config['vocabulary'];answers=config['answers']
    model=SiameseVQA(len(vocab)+2,len(answers));model.load_state_dict(torch.load(folder/'weights.pt',map_location='cpu',weights_only=True))
    def encode(r):
        imgs=[read_image(ROOT/p,f'img{i}',{}) for i,p in enumerate(r['paths'])]
        return image_tensor(imgs[0]),image_tensor(imgs[1]),question_tensor(r['query'],vocab),answers.index(r['answer'])
    train=[encode(r) for r in rows if r['metadata']['image_id']!=groups[-1]];val=[encode(r) for r in rows if r['metadata']['image_id']==groups[-1]]
    a,b,q=[torch.stack([r[i] for r in train]) for i in range(3)];y=torch.tensor([r[3] for r in train])
    def score():
        model.eval()
        with torch.inference_mode():return sum(int(int(model(x[None],z[None],q[None]).argmax())==label) for x,z,q,label in val)/len(val)
    before=score();opt=torch.optim.AdamW(model.parameters(),lr=.0001,weight_decay=.01)
    for step in range(120):
        model.train();opt.zero_grad();loss=torch.nn.functional.cross_entropy(model(a,b,q),y);loss.backward();opt.step()
    result={'before_validation_accuracy':before,'after_validation_accuracy':score(),'steps':120,'unique_pairs':len(groups),'promoted':False,'reason':'Only two labelled image pairs exist; no independent, representative validation population. Candidate is not deployed. Original weights also saw these pairs historically.'}
    (ROOT/'training/change_refinement_results.json').write_text(json.dumps(result,indent=2));print(result,flush=True)
if __name__=='__main__':main()
