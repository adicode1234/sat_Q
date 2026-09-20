import numpy as np


def run(bundle,call):
    from gateway.spatial import pack_mask,heatmap
    a,b=bundle['images'];x,y=a['array'],b['array']
    valid=np.isfinite(x).all(0)&np.isfinite(y).all(0)
    if not valid.any():raise ValueError('Temporal images have no shared valid pixels')
    lo,hi=np.percentile(np.concatenate([x[:,valid].ravel(),y[:,valid].ravel()]),[2,98])
    delta=np.mean(np.abs(np.nan_to_num(y-x)),axis=0)/max(float(hi-lo),1e-6)
    mask=valid&(delta>call.get('params',{}).get('threshold',.25))
    return {'answer':f'Full-resolution candidate change mask: {int(mask.sum())} changed pixels ({mask.sum()/valid.sum():.1%} of comparable pixels). Appearance differences do not establish semantic change.',
            'neural_confidence':0,'claims':[],'mode':'deterministic_spatial_change_mask','overlay':encode(mask),
            'raw_mask':pack_mask(mask),'changed_pixel_count':int(mask.sum()),'comparable_pixel_count':int(valid.sum()),
            'heatmap':heatmap(np.where(valid,np.clip(delta,0,1),np.nan),b['id'],'Heuristic normalized appearance difference; not probability')}

def encode(mask, image_id='img2'):
    # Downsample only display, retain measured fraction at original resolution.
    stride=max(1,int(np.ceil(max(mask.shape)/192)))
    return {'type':'mask','data':mask[::stride,::stride].astype('uint8').tolist(),
            'width':mask.shape[1],'height':mask.shape[0],'image_id':image_id,
            'label':'Candidate appearance change (not ground truth)'}
