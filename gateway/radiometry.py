"""Explicit radiometric handling: conversion is not calibration of raw SAR DN."""
import numpy as np

def prepare(image,options):
    md=image['raster_metadata'];tags={str(k).lower():v for k,v in md.get('tags',{}).items()}
    sensor=options.get('sensor') or tags.get('spacecraft_name') or tags.get('satellite') or tags.get('sensor')
    image['sensor']=sensor;image['radiometry']={'sensor':sensor,'units_source':'user declaration' if image['sar_units']!='unknown' else 'unknown'}
    if image['modality']=='optical':
        factor=options.get('reflectance_scale');offset=options.get('reflectance_offset',0)
        normalized=tags.get('satquery_normalized')=='1'
        if factor is None and not normalized and all(s==1 for s in md.get('scales',[1])):
            quant=tags.get('boa_quantification_value') or tags.get('quantification_value')
            if quant and float(quant)>0:
                # Offset-bearing Sentinel products need their per-band BOA offsets.
                if not any('offset' in k for k in tags):factor=1/float(quant)
        if factor is not None:
            if not isinstance(factor,(float,int)) or isinstance(factor,bool) or not np.isfinite(factor) or factor<=0:raise ValueError('reflectance_scale must be a positive finite number')
            if not isinstance(offset,(float,int)) or not np.isfinite(offset):raise ValueError('reflectance_offset must be finite')
            if any(s!=1 for s in md.get('scales',[1])) or any(o!=0 for o in md.get('offsets',[0])):
                raise ValueError('Raster scale/offset already applied; do not supply a second reflectance conversion')
            image['array']=image['array']*factor+offset
            image['radiometry'].update(reflectance_conversion={'scale':factor,'offset':offset,'source':'user_declared' if options.get('reflectance_scale') is not None else 'raster_quantification_metadata'})
        image['radiometry']['reflectance_scale_known']=bool(factor is not None or any(s!=1 for s in md.get('scales',[1])) or image.get('source_type')=='synthetic_demo')
    else:
        if image['sar_units']=='linear':
            image['array']=np.where(image['array']>0,image['array'],np.nan)
        image['radiometry']['note']='Declared calibrated power only. Raw DN requires the sensor calibration LUT and terrain correction upstream.'
    finite=image['array'][np.isfinite(image['array'])]
    image['radiometry']['value_percentiles']=np.percentile(finite,[1,50,99]).tolist() if finite.size else []
