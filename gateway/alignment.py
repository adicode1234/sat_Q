"""Translation diagnostic on coarse edge maps; never certifies co-registration."""
import numpy as np


def estimate_pair(a,b):
    stride=max(1,int(np.ceil(max(a['shape'])/256)))
    def edges(image):
        data=image['array'][0,::stride,::stride].astype(float)
        valid=np.isfinite(data)
        if valid.mean()<.5 or min(data.shape)<8:return None
        data=np.nan_to_num(data,nan=float(np.nanmedian(data)))
        lo,hi=np.percentile(data,[5,95])
        if hi-lo<1e-8:return None
        data=np.clip((data-lo)/(hi-lo),0,1)
        gx,gy=np.gradient(data);edge=np.hypot(gx,gy)
        edge-=edge.mean()
        return edge
    x,y=edges(a),edges(b)
    common=float((np.isfinite(a['array'][0])&np.isfinite(b['array'][0])).mean())
    result={'overlap_valid_fraction':common,'estimated_shift_pixels':None,'score':None,
            'method':'Coarse gradient-magnitude phase correlation; translation only, not a registration certificate.',
            'cross_sensor':a['modality']!=b['modality']}
    if x is None or y is None:return {**result,'warning':'Insufficient texture/coverage to estimate alignment.'}
    cross=np.fft.fft2(x)*np.conj(np.fft.fft2(y));cross/=np.maximum(np.abs(cross),1e-12)
    corr=np.fft.ifft2(cross).real;peak=np.unravel_index(np.argmax(corr),corr.shape)
    shift=[int((p if p<=n//2 else p-n)*stride) for p,n in zip(peak,corr.shape)]
    score=float(np.clip(corr[peak],0,1))
    sidelobes=corr.copy()
    for dy in range(-2,3):
        for dx in range(-2,3):sidelobes[(peak[0]+dy)%corr.shape[0],(peak[1]+dx)%corr.shape[1]]=np.nan
    psr=float((corr[peak]-np.nanmean(sidelobes))/max(float(np.nanstd(sidelobes)),1e-12))
    result.update(estimated_shift_pixels={'x':shift[1],'y':shift[0]},score=score,
                  peak_to_sidelobe_ratio=psr,
                  warning='Different sensors/seasons may have unrelated edges; review manually.' if result['cross_sensor'] or score<.25 else
                          'Potential misalignment: estimated translation exceeds two sampled pixels.' if max(map(abs,shift))>2*stride else None)
    return result
