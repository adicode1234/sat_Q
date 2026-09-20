"""Bounded real-data download from the original Sen1Floods11 bucket; official splits."""
import csv,hashlib,io,json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
BASE='https://storage.googleapis.com/sen1floods11/v1.1/'
S2=['coastal','blue','green','red','rededge1','rededge2','rededge3','nir','nir_narrow','water_vapor','cirrus','swir','swir2']

def main():
    folder=ROOT/'data/sen1floods11';folder.mkdir(parents=True,exist_ok=True);samples=[]
    for split,count,source in [('train',96,'train'),('validation',24,'valid'),('test',24,'test')]:
        url=BASE+f'splits/flood_handlabeled/flood_{source}_data.csv'
        r=requests.get(url,timeout=60);r.raise_for_status();(folder/f'{split}_source.csv').write_text(r.text)
        groups={}
        for row in csv.reader(io.StringIO(r.text)):
            if len(row)<2:continue
            groups.setdefault(row[0].split('_')[0],[]).append(row)
        selected=[g[n] for n in range(max(map(len,groups.values()))) for _,g in sorted(groups.items()) if n<len(g)][:count]
        for s1,label in selected:
            key=s1.replace('_S1Hand.tif','')
            samples.append({'id':key,'split':split,'source_split_url':url,'s1':f'data/sen1floods11/{key}_S1Hand.tif',
                's2':f'data/sen1floods11/{key}_S2Hand.tif','label':f'data/sen1floods11/{label}',
                'options':[{'modality':'optical','sensor':'sentinel-2','bands':S2,'reflectance_scale':.0001,'coregistered':True,'benchmark_source':BASE},
                           {'modality':'SAR','sensor':'sentinel-1','bands':['vv','vh'],'sar_units':'db','coregistered':True,'benchmark_source':BASE}]})
    assert len({s['id'] for s in samples})==len(samples),'Training/validation/test chip overlap'
    jobs=[(key,s[key]) for s in samples for key in ('s1','s2','label')]
    def fetch(job):
        key,rel=job;path=ROOT/rel;layer={'s1':'S1Hand','s2':'S2Hand','label':'LabelHand'}[key]
        if not path.exists():
            for attempt in range(3):
                try:
                    r=requests.get(BASE+f'data/flood_events/HandLabeled/{layer}/'+path.name,timeout=90);r.raise_for_status()
                    path.with_suffix('.part').write_bytes(r.content);path.with_suffix('.part').replace(path);break
                except requests.RequestException:
                    if attempt==2:raise
        return rel,hashlib.sha256(path.read_bytes()).hexdigest()
    with ThreadPoolExecutor(max_workers=4) as pool:
        hashes=dict(pool.map(fetch,jobs))
    for s in samples:s['sha256']={k:hashes[s[k]] for k in ('s1','s2','label')}
    (folder/'manifest.json').write_text(json.dumps(samples,indent=2));print('Downloaded',len(samples),'real aligned optical/SAR/label chips',flush=True)
if __name__=='__main__':main()
