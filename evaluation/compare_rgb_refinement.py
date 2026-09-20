"""Compare frozen RGB water weights with the previously deployed colour rules."""
import importlib.util,json
from pathlib import Path
import numpy as np
import rasterio
from gateway.validation import read_image
from models.rgb_water import pixels
from models.rgb_water_expert import predict,ROOT
from evaluation.evaluate_rgb_water import metrics

def main():
    spec=importlib.util.spec_from_file_location('old_rgb',str(ROOT/'evaluation/legacy_rgb_baseline.py'));old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    samples=json.loads((ROOT/'data/sen1floods11/manifest.json').read_text());result={};rng=np.random.default_rng(412)
    for split in ('validation','test'):
        baseline=[];candidate=[]
        for row in [r for r in samples if r['split']==split]:
            im=read_image(ROOT/row['s2'],'img1',row['options'][0]);a,valid=pixels(im)
            with rasterio.open(ROOT/row['label']) as f:y=f.read(1)
            rgb={**im,'array':(a/255).transpose(2,0,1),'bands':['red','green','blue'],'radiometry':{},'raster_metadata':{'format':'PNG'}}
            before,_=old.predict(rgb);after,threshold=predict(a,valid);valid &= (y==0)|(y==1)
            n=int(valid.sum());ids=rng.choice(n,min(n,10000),replace=False)
            baseline.append((before[valid][ids],y[valid][ids]));candidate.append((after[valid][ids],y[valid][ids]))
        result[split]={'baseline':metrics(baseline,.5),'candidate':metrics(candidate,threshold)}
    result['promoted']=result['validation']['candidate']['iou']>result['validation']['baseline']['iou']
    result['scope']='Fixed RGB renderings of official Sen1Floods11 validation/test chips; no evaluation-driven hyperparameter adjustment. RGB sensor transfer remains unvalidated.'
    (ROOT/'evaluation/rgb_refinement_comparison.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
if __name__=='__main__':main()
