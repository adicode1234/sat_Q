"""Independent RGB-only water validation/test evaluation on Sen1Floods11 labels.

Checkpoint is pretrained on a different RGB dataset. No test-set tuning occurs.
Sen1Floods11 views are generated with a fixed, documented reflectance display scale.
"""
import json,time
from pathlib import Path
import numpy as np
import rasterio
from gateway.validation import read_image
from models.rgb_water import predict
ROOT=Path(__file__).resolve().parents[1]

def metrics(rows,threshold):
    tp=fp=fn=tn=0;brier=0;n=0
    for p,y in rows:
        pred=p>=threshold;tp+=int((pred&(y==1)).sum());fp+=int((pred&(y==0)).sum())
        fn+=int((~pred&(y==1)).sum());tn+=int((~pred&(y==0)).sum())
        brier+=float(((p-y)**2).sum());n+=len(y)
    return {'iou':tp/max(tp+fp+fn,1),'f1':2*tp/max(2*tp+fp+fn,1),'precision':tp/max(tp+fp,1),
            'recall':tp/max(tp+fn,1),'brier':brier/max(n,1),'tp':tp,'fp':fp,'fn':fn,'tn':tn,'pixels':n}

def main():
    samples=json.loads((ROOT/'data/sen1floods11/manifest.json').read_text())
    folder=ROOT/'evaluation/rgb_water';folder.mkdir(exist_ok=True)
    data={};timings=[];ids={}
    for split in ('validation','test'):
        data[split]=[];ids[split]=[]
        for row in [r for r in samples if r['split']==split]:
            image=read_image(ROOT/row['s2'],'img1',row['options'][0]);t=time.perf_counter();p,valid=predict(image)
            timings.append(time.perf_counter()-t)
            with rasterio.open(ROOT/row['label']) as src:y=src.read(1)
            assert p.shape==y.shape
            valid &= (y==0)|(y==1)
            data[split].append((p[valid],y[valid]));ids[split].append(row['id'])
            print(split,row['id'],round(timings[-1],2),flush=True)
    threshold=float(max(np.linspace(.15,.85,29),key=lambda t:metrics(data['validation'],t)['iou']))
    result={'checkpoint':'sat-water ResNet34 U-Net 256','threshold':threshold,
            'validation':metrics(data['validation'],threshold),'test':metrics(data['test'],threshold),
            'default_threshold_validation':metrics(data['validation'],.5),'chips':ids,
            'median_latency_s':float(np.median(timings[1:])),
            'scope':'24 validation and 24 test Sen1Floods11 RGB renderings; all valid label pixels. A domain-transfer test, not universal RGB accuracy. No local model-weight training.',
            'calibration':'Threshold fit on validation only; softmax is NOT calibrated probability of correctness.'}
    (folder/'evaluation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
