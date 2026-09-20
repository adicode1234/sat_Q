"""Acquire 16 actual VRSBench train VQA examples; never use evaluation images."""
import json,zipfile
from pathlib import Path
from evaluation.fetch_samples import RemoteZip,get
ROOT=Path(__file__).resolve().parents[1]
def main():
    source='https://huggingface.co/datasets/xiang709/VRSBench'
    rows=get(source+'/resolve/main/VRSBench_train.json').json()
    config=json.loads((ROOT/'models/checkpoints/vilt/config.json').read_text())
    labels=config['label2id'];selected=[]
    eval_images=set(p for r in json.loads((ROOT/'evaluation/samples.json').read_text()) for p in r['paths'])
    with zipfile.ZipFile(RemoteZip(source+'/resolve/main/Images_train.zip')) as archive:
        lookup={Path(n).name:n for n in archive.namelist() if n.endswith('.png')}
        for row in rows:
            question=row['conversations'][0]['value'];answer=row['conversations'][1]['value'].lower().strip()
            if '[vqa]' not in question or answer not in labels:continue
            filename=row['image']
            if any(p.endswith('/'+filename) for p in eval_images):raise ValueError('Training image overlaps evaluation slice')
            folder=ROOT/'data/vrsbench/train';folder.mkdir(parents=True,exist_ok=True);path=folder/filename
            if not path.exists():path.write_bytes(archive.read(lookup[filename]))
            selected.append({'image':path.relative_to(ROOT).as_posix(),'question':question.replace('<image>','').replace('[vqa]','').strip(),
                             'answer':answer,'split':'train','source':source,'source_image':filename})
            if len(selected)==16:break
    (ROOT/'data/vrsbench/train.jsonl').write_text('\n'.join(json.dumps(row) for row in selected),encoding='utf-8')
    print(f'Downloaded {len(selected)} genuine VRSBench train questions')
if __name__=='__main__':main()
