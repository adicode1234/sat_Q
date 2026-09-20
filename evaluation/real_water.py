"""All three real water pathways evaluated through the production controller."""
import json
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject,Resampling
from affine import Affine
from controller.pipeline import run_pipeline
from gateway.spatial import unpack_mask
ROOT=Path(__file__).resolve().parents[1]

def main():
    samples=[r for r in json.loads((ROOT/'data/sen1floods11/manifest.json').read_text()) if r['split']=='test'];rows=[]
    for index,row in enumerate(samples):
        with rasterio.open(ROOT/row['label']) as src:
            label=src.read(1);label_transform=src.transform;label_crs=src.crs
        for kind,keys,opts,scenario in [('optical',['s2'],row['options'][:1],'SINGLE'),('sar',['s1'],row['options'][1:],'SINGLE'),('joint',['s2','s1'],row['options'],'CROSS_MODAL_PAIR')]:
            out=run_pipeline([ROOT/row[k] for k in keys],opts,scenario,'What areas are covered by water?')
            assert out['task']=='WATER_ANALYSIS',out['execution_trace']
            specialist=out['specialists'][0];assert specialist['status']=='complete',specialist
            pred=unpack_mask(specialist['raw_mask'])
            grid=next(i for i in out['input']['images'] if i['id']==specialist['overlay']['image_id'])
            y=np.full(pred.shape,-1,dtype='int16')
            reproject(label,y,src_transform=label_transform,src_crs=label_crs,src_nodata=-1,
                      dst_transform=Affine(*grid['transform']),dst_crs=grid['crs'],dst_nodata=-1,resampling=Resampling.nearest)
            valid=(y==0)|(y==1)
            tp=int((pred&(y==1)&valid).sum());fp=int((pred&(y==0)&valid).sum());fn=int((~pred&(y==1)&valid).sum())
            rows.append({'id':row['id'],'kind':kind,'tp':tp,'fp':fp,'fn':fn,'trust':out['trust_score'],'mode':specialist['mode'],
                         'decision':out['decision']['status'],'evidence_coverage':out['confidence_breakdown']['coverage'],
                         'evaluated_label_pixels':int(valid.sum()),'output_shape':list(pred.shape),
                         'trace_actions':[e['action'] for e in out['execution_trace']],'early_development_chip':index<8})
        print(index+1,'/',len(samples),row['id'],flush=True)
    result={'scope':'Full valid label pixels of 24 official test chips; first 8 were inspected during early development, remaining 16 newly evaluated. Not a full benchmark or sensor-transfer validation.', 'rows':rows,'metrics':{}}
    for cohort in ('all_24','new_16'):
        result['metrics'][cohort]={}
        for kind in ('optical','sar','joint'):
            selected=[r for r in rows if r['kind']==kind and (cohort=='all_24' or not r['early_development_chip'])]
            tp,fp,fn=[sum(r[k] for r in selected) for k in ('tp','fp','fn')]
            result['metrics'][cohort][kind]={'iou':tp/max(tp+fp+fn,1),'f1':2*tp/max(2*tp+fp+fn,1),'precision':tp/max(tp+fp,1),'recall':tp/max(tp+fn,1),'completed':len(selected)}
    (ROOT/'evaluation/real_water_summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result['metrics'],indent=2))
if __name__=='__main__':main()
