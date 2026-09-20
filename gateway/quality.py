"""Conservative input usability indicators, not a trained cloud classifier."""
import numpy as np


def assess(image):
    a = image['array']
    finite = np.isfinite(a)
    coverage = float(finite.all(axis=0).mean())
    band_quality = []
    warnings = []
    for band, values in zip(image['bands'], a):
        v = values[np.isfinite(values)]
        lo, hi = np.percentile(v, [2, 98]) if v.size else (None, None)
        band_quality.append({'band': band, 'valid_fraction': float(np.isfinite(values).mean()),
                             'p02': float(lo) if lo is not None else None,
                             'p98': float(hi) if hi is not None else None,
                             'low_contrast': bool(v.size and hi-lo <= max(abs(float(hi)), 1)*1e-5)})
    if coverage < .5: warnings.append('More than half the raster lacks common valid band coverage.')
    if any(b['valid_fraction'] == 0 for b in band_quality): warnings.append('One or more bands contain no valid values.')
    if all(b['low_contrast'] for b in band_quality): warnings.append('Near-constant raster: little usable contrast.')
    if min(image['shape']) < 32: warnings.append('Tiny raster: semantic inference may be unreliable.')
    cloud = saturation = None
    names = image['bands']
    if image['modality'] == 'optical' and all(b in names for b in ('red','green','blue')):
        rgb = a[[names.index(b) for b in ('red','green','blue')]]
        valid = np.isfinite(rgb).all(axis=0)
        if valid.any() and np.nanmin(rgb) >= 0 and np.nanmax(rgb) <= 1.5:
            cloud = float(((rgb.mean(0) > .8) & (rgb.std(0) < .08))[valid].mean())
            saturation = float((rgb >= .995).all(0)[valid].mean())
            if cloud > .5: warnings.append('Heavy bright-neutral coverage: possible cloud/snow, not a cloud classification.')
    score = coverage * (1 - (cloud or 0)*.7)
    if all(b['low_contrast'] for b in band_quality): score *= .2
    if min(image['shape']) < 32: score *= .5
    return {'score': round(score,4), 'valid_fraction': coverage, 'bands': band_quality,
            'cloud_proxy_fraction': cloud, 'saturation_proxy_fraction': saturation,
            'warnings': warnings, 'semantics': 'Heuristic usability score; cloud proxy can confuse snow or bright roofs.'}


def suggest_modality(image):
    names = ' '.join(image['bands']) + ' ' + image.get('filename','').lower()
    values = image['array'][np.isfinite(image['array'])]
    if any(s in names for s in ('ndvi','ndwi','ndbi')):
        return 'NDVI/SPECTRAL_INDEX'
    if any(s in image['bands'] for s in ('vv','vh','hh','hv','sigma0','gamma0')):
        return 'SAR'
    if image['array'].shape[0] > 3 and any(s in image['bands'] for s in ('nir','swir')):
        return 'MULTISPECTRAL'
    if all(s in image['bands'] for s in ('red','green','blue')):
        return 'OPTICAL'
    if image['array'].shape[0] <= 2 and values.size and np.percentile(values,95) < 0:
        return 'SAR'
    return 'UNKNOWN'
