"""Index-based measurements and multi-date trajectories, never neural inference."""
import numpy as np
from verification.engine import summaries
from gateway.spatial import region_features,pack_mask
from models.change_mask.model import encode


def run(bundle,call):
    unavailable=bundle.get('validation',{}).get('unavailable_tasks',[])
    if unavailable:
        return {'answer':', '.join(unavailable)+' unavailable: required spectral bands are missing on one or more dates. Visual analysis remains available.',
                'neural_confidence':0,'claims':[],'mode':'measurement_unavailable','measurements':[], 'trend':None}
    stats,maps=summaries(bundle);sequence=[];raw=None;overlay=None
    query=call['query'].lower()
    index,threshold=(('NDBI',.1) if any(w in query for w in ('ndbi','built','building')) else
                     ('NDVI',.3) if any(w in query for w in ('vegetation','ndvi','green')) else ('NDWI',.15))
    optical_threshold=threshold
    for image in bundle['images']:
        threshold=optical_threshold
        values=maps[image['id']].get(index)
        if values is None and index=='NDWI' and image['modality']=='SAR' and 'SAR' in maps[image['id']]:
            values=-maps[image['id']]['SAR'];threshold=17;measure='SAR smooth-surface proxy'
        else:measure=index+' threshold proxy'
        if values is None:
            sequence.append({'image_id':image['id'],'date':image['date'],'fraction':None,'area_m2':None,'reason':'Required bands or SAR calibration unavailable'})
            continue
        valid=np.isfinite(values);mask=valid&(values>threshold)
        geo=region_features(image,mask,measure)
        sequence.append({'image_id':image['id'],'date':image['date'],'fraction':float(mask.sum()/valid.sum()) if valid.any() else None,
                         'area_m2':geo.get('area_m2'),'measurement':measure,'threshold':threshold,'valid_pixels':int(valid.sum())})
        raw=pack_mask(mask);overlay=encode(mask,image['id']);overlay['label']=measure
    usable=[r for r in sequence if r['fraction'] is not None]
    trend=None
    if len(usable)>1:
        delta=usable[-1]['fraction']-usable[0]['fraction']
        trend={'direction':'increase' if delta>.01 else 'decrease' if delta<-.01 else 'approximately stable',
               'fraction_delta':delta,'description':'Endpoint comparison of measurement proxies, not a causal or statistical significance claim.'}
    return {'answer':('Measured proxy trajectory: '+trend['direction']+'. ' if trend else 'Physical measurement proxies are available. ' if usable else 'Required physical measurements are unavailable. ')+
                     ' '.join(f"{m['image_id']}: {m['measurement']} covers {m['fraction']:.1%} of {m['valid_pixels']:,} valid pixels." for m in usable)+' '+
                     'Threshold classes are not ground-truth land cover; seasonal and sensor differences can change them.',
            'neural_confidence':0,'claims':[],'mode':'deterministic_measurement','measurements':sequence,'trend':trend,
            'overlay':overlay,'raw_mask':raw,'physical_statistics':stats}
