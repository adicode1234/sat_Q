"""Official RSVQA-LR test importer. Preserves raw answers and source metadata."""
import argparse,hashlib,json,zipfile
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
SOURCE='https://zenodo.org/records/6344334'


def main():
    p=argparse.ArgumentParser();p.add_argument('--limit',type=int,default=64);args=p.parse_args()
    folder=ROOT/'data/rsvqa/official';folder.mkdir(parents=True,exist_ok=True)
    files=['LR_split_test_images.json','LR_split_test_questions.json','LR_split_test_answers.json','Images_LR.zip']
    for name in files:
        path=folder/name
        if not path.exists():
            with requests.get(f'https://zenodo.org/api/records/6344334/files/{name}/content',stream=True,timeout=90) as r:
                r.raise_for_status()
                with path.with_suffix('.part').open('wb') as f:
                    for chunk in r.iter_content(1024*1024):f.write(chunk)
            path.with_suffix('.part').replace(path)
    def active(name,key):return {x['id']:x for x in json.loads((folder/name).read_text())[key] if x.get('active')}
    images=active(files[0],'images');questions=active(files[1],'questions');answers=active(files[2],'answers')
    # Round-robin across all held-out images instead of taking one image's questions.
    groups={i:[q for q in questions.values() if q['img_id']==i] for i in images}
    rows=[group[(n+offset)%len(group)] for n in range(max(map(len,groups.values()))) for offset,group in enumerate(groups.values()) if n<len(group)]
    chosen=rows if args.limit==0 else rows[:args.limit];samples=[]
    with zipfile.ZipFile(folder/'Images_LR.zip') as archive:
        for q in chosen:
            name=f"Images_LR/{q['img_id']}.tif";path=folder/name;path.parent.mkdir(exist_ok=True)
            if not path.exists():path.write_bytes(archive.read(name))
            samples.append({'dataset':'RSVQA','split':'official_test','id':str(q['id']),
                'paths':[path.relative_to(ROOT).as_posix()],'options':[{'modality':'optical','bands':['red','green','blue'],'benchmark_source':SOURCE}],
                'scenario':'SINGLE','query':q['question'],'answer':answers[q['answers_ids'][0]]['answer'],
                'source':SOURCE,'source_metadata':{'image_id':q['img_id'],'question_type':q['type'],'image':images[q['img_id']]},
                'sha256':[hashlib.sha256(path.read_bytes()).hexdigest()]})
    manifest=ROOT/'evaluation/samples.json';existing=json.loads(manifest.read_text()) if manifest.exists() else []
    manifest.write_text(json.dumps([s for s in existing if s['dataset']!='RSVQA']+samples,indent=2),encoding='utf-8')
    status={'source':SOURCE,'split':'official_test','available_questions':len(rows),'selected_questions':len(samples),
            'selected_images':len({s['source_metadata']['image_id'] for s in samples}),
            'selection':'deterministic round-robin across active test images, offset question index by image order','full_split':len(samples)==len(rows)}
    (ROOT/'evaluation/rsvqa_status.json').write_text(json.dumps(status,indent=2));print(json.dumps(status,indent=2))
    log_path=ROOT/'evaluation/data_status.json';log=json.loads(log_path.read_text()) if log_path.exists() else []
    log=[r for r in log if r['dataset']!='RSVQA']+[{'dataset':'RSVQA','status':'downloaded','count':len(samples),**status}]
    log_path.write_text(json.dumps(log,indent=2),encoding='utf-8')
if __name__=='__main__':main()
