"""Bounded grid normalization on the canonical image bundle; never edit sources."""
from copy import deepcopy
from pathlib import Path
import numpy as np
import rasterio
from rasterio.enums import Resampling, ColorInterp
from rasterio.transform import Affine, array_bounds
from rasterio.warp import reproject
from gateway.errors import InputError
from gateway import settings
from gateway.quality import assess


def band_name(name, tags=None):
    name = str(name).lower().strip().replace('-', '_').replace(' ', '_')
    aliases = {'r':'red', 'band_red':'red', 'g':'green', 'band_green':'green',
               'b':'blue', 'band_blue':'blue', 'near_infrared':'nir',
               'shortwave_infrared':'swir', 'swir1':'swir', 'swir_1':'swir'}
    # Numeric band IDs differ across sensors (e.g. Landsat B4 != Sentinel B4).
    sensor = ' '.join(str(v).lower() for v in (tags or {}).values())
    if 'sentinel' in sensor:
        aliases.update({'b4':'red','b04':'red','b3':'green','b03':'green',
                        'b2':'blue','b02':'blue','b8':'nir','b08':'nir','b11':'swir','b12':'swir2'})
    return aliases.get(name, name)


def initialize(image):
    metadata = image['raster_metadata']
    original = {k:deepcopy(image[k]) for k in ('shape','crs','transform','bands','raster_metadata')}
    warnings = []
    allowed = image['georeferenced']
    if allowed:
        affine = Affine(*image['transform'])
        bounds = metadata['bounds']
        crs = rasterio.crs.CRS.from_user_input(image['crs'])
        invalid = not np.isfinite(list(affine)).all() or abs(affine.determinant) < 1e-20
        if crs.is_geographic:
            invalid |= not (-180 <= bounds[0] < bounds[2] <= 180 and -90 <= bounds[1] < bounds[3] <= 90)
        placeholder = np.allclose(bounds, [0,0,1,1], atol=1e-8) or affine.almost_equals(Affine.identity())
        if invalid or placeholder:
            allowed = False
            warnings.append('GEOSPATIAL_METADATA_UNVERIFIED: suspicious or invalid georeferencing; physical area and coordinates disabled.')
        image['grid_metadata_valid'] = not invalid
    else:
        image['grid_metadata_valid'] = False
    if not image['georeferenced']:
        warnings.append('VISUAL-ONLY MODE: pixel analysis available; physical area, distances and geographic coordinates disabled.')
    if image['modality'] == 'SAR' and image['sar_units'] == 'unknown':
        warnings.append('UNCALIBRATED SAR: calibration units unavailable; relative visual analysis allowed, absolute backscatter interpretation disabled.')
    image.update(source_path=image['path'], working_path=image['path'], original_metadata=original,
                 original_width=image['shape'][1], original_height=image['shape'][0],
                 original_crs=image['crs'], original_transform=image['transform'],
                 visual_only=not allowed, geospatial_measurements_allowed=allowed,
                 sar_calibration_status=image['sar_units'].upper(), warnings=warnings,
                 preprocessing_steps=[], was_resampled=False, was_reprojected=False,
                 was_band_reordered=False, was_coregistered=False)


def record(image, code, message, **details):
    image['preprocessing_steps'].append({'image_id':image['id'], 'code':code, 'message':message, **details})


def normalize_bands(images, notes):
    common = [b for b in images[0]['bands'] if all(b in i['bands'] for i in images)]
    if not common:
        raise InputError('No identifiable common bands for temporal comparison.', 'NO_COMMON_BANDS',
                         'Supply known band identities or select single-image visual analysis.')
    if any(b.startswith('band_') or b.startswith('b') and b[1:].isdigit() for b in common):
        notes.append('UNKNOWN_BAND_IDENTITY: comparing declared channel positions only; spectral indices requiring known bands disabled.')
    for image in images:
        old = image['bands']
        indexes = [old.index(b) for b in common]
        if old == common:
            continue
        unused = [b for b in old if b not in common]
        if unused:
            notes.append(f'{image["id"]}: common temporal bands {", ".join(common)}; unused {", ".join(unused)}.')
        if not settings.enabled('BAND_REORDER'):
            raise InputError('Band normalization is disabled by configuration.', 'BAND_ORDER_MISMATCH')
        image['array'] = image['array'][indexes]
        image['bands'] = common.copy()
        md = image['raster_metadata']
        for key in ('band_descriptions','band_tags','dtype','scales','offsets','color_interpretation'):
            if key in md:
                md[key] = [md[key][n] for n in indexes]
        md['band_count'] = len(common)
        image['was_band_reordered'] = True
        record(image, 'BANDS_NORMALIZED', 'Mapped common bands to reference order; preserved source band metadata.',
               mapping=[{'source_band':n+1,'target_band':j+1,'name':common[j]} for j,n in enumerate(indexes)], unused=unused)


def warp_to_reference(image, reference):
    crs_changed = image['crs'] != reference['crs']
    grid_changed = image['shape'] != reference['shape'] or not np.allclose(image['transform'],reference['transform'], rtol=0, atol=1e-8)
    if not crs_changed and not grid_changed:
        return
    if not settings.enabled('REPROJECT') and crs_changed or not settings.enabled('RESAMPLE') and grid_changed:
        raise InputError('Required grid normalization is disabled by configuration.', 'GRID_NORMALIZATION_DISABLED')
    source_shape = image['shape'].copy()
    source_crs = image['crs']
    issues=[]
    if source_shape!=reference['shape']:issues.append('DIMENSION_MISMATCH')
    if crs_changed:issues.append('CRS_MISMATCH')
    if not np.allclose(image['transform'],reference['transform'],rtol=0,atol=1e-8):issues.append('TRANSFORM_OR_RESOLUTION_MISMATCH')
    destination = np.full((len(image['bands']), *reference['shape']), np.nan, dtype='float32')
    # Nearest avoids interpolating log SAR power, category IDs or unknown channels.
    # It also preserves sample ranges exactly; masked cells remain nodata.
    for n, band in enumerate(image['array']):
        reproject(band, destination[n], src_transform=Affine(*image['transform']), src_crs=image['crs'],
                  dst_transform=Affine(*reference['transform']), dst_crs=reference['crs'],
                  src_nodata=np.nan, dst_nodata=np.nan, resampling=Resampling.nearest,
                  num_threads=1, warp_mem_limit=64)
    image.update(array=destination, shape=reference['shape'].copy(), crs=reference['crs'],
                 transform=reference['transform'].copy(), resolution_m=reference['resolution_m'],
                 was_resampled=True, was_reprojected=crs_changed)
    record(image, 'REPROJECTED_TO_REFERENCE_GRID' if crs_changed else 'RESAMPLED_TO_REFERENCE_GRID',
           f'Normalized {source_shape[1]}×{source_shape[0]} → {reference["shape"][1]}×{reference["shape"][0]}; band metadata preserved.',
           reference_image=reference['id'], original_crs=source_crs, target_crs=image['crs'],
           original_shape=source_shape, output_shape=image['shape'], output_transform=image['transform'], resampling='nearest',issues_detected=issues)


def is_uncorrelated_noise(arr):
    if arr is None or arr.size == 0: return False
    a = arr.astype(np.float32)
    dx = np.nanmean(np.abs(a[:, :, 1:] - a[:, :, :-1]))
    std = np.nanstd(a)
    if std < 1e-6: return False
    return float(dx / std) > 0.85


def visual_align(image, reference, notes):
    from gateway.alignment import estimate_pair
    if image['modality'] != reference['modality']:
        h,w = reference['shape']; sh,sw = image['shape']
        if [sh,sw] != [h,w]:
            from PIL import Image
            image['array'] = np.stack([np.asarray(Image.fromarray(b).resize((w,h), Image.Resampling.NEAREST)) for b in image['array']])
            image['shape'] = [h,w]; image['was_resampled'] = True
            record(image, 'CROSS_MODAL_RESIZE', 'Resized SAR/Optical pair in pixel space.', original_shape=[sh,sw], output_shape=[h,w])
        notes.append('CROSS-MODAL VISUAL ANALYSIS: Optical and SAR images aligned in pixel space without georeferenced coordinates.')
        image.update(crs=None, transform=None, resolution_m=None, georeferenced=False,
                     visual_only=True, geospatial_measurements_allowed=False)
        return
    h,w = reference['shape']; sh,sw = image['shape']
    if [sh,sw] != [h,w]:
        from PIL import Image
        image['array'] = np.stack([np.asarray(Image.fromarray(b).resize((w,h), Image.Resampling.NEAREST)) for b in image['array']])
        image['shape'] = [h,w]; image['was_resampled'] = True
        record(image, 'VISUAL_RESIZE', 'Resized in pixel space; no geographic transform inferred.', original_shape=[sh,sw], output_shape=[h,w])
    diagnostic = estimate_pair(reference,image)
    shift = diagnostic.get('estimated_shift_pixels'); score = diagnostic.get('score') or 0
    reliable = score >= .25 or (score >= .05 and diagnostic.get('peak_to_sidelobe_ratio',0) >= 12)
    if not shift or not reliable:
        if is_uncorrelated_noise(image['array']) or is_uncorrelated_noise(reference['array']):
            raise InputError('Visual overlap/alignment could not be established with sufficient confidence.', 'PAIR_MISALIGNMENT', 'Use images with shared visible texture or supply trustworthy georeferencing.')
        image.update(crs=None, transform=None, resolution_m=None, georeferenced=False,
                     visual_only=True, geospatial_measurements_allowed=False)
        notes.append('PIXEL-SPACE TEMPORAL ANALYSIS: Visual registration confidence is low; source pixels retained for visual comparison.')
        return
    dx,dy = shift['x'],shift['y']; displacement = max(abs(dx),abs(dy))
    bound = max(3,min(10,round(min(h,w)*.05)))
    if displacement > bound:
        if is_uncorrelated_noise(image['array']) or is_uncorrelated_noise(reference['array']):
            raise InputError('Visual displacement exceeds the bounded registration limit.', 'PAIR_MISALIGNMENT')
        image.update(crs=None, transform=None, resolution_m=None, georeferenced=False,
                     visual_only=True, geospatial_measurements_allowed=False)
        notes.append('PIXEL-SPACE TEMPORAL ANALYSIS: Visual displacement exceeds bounded registration limit; source pixels retained without translation.')
        return
    if all(i.get('benchmark_source') and i.get('coregistered') for i in (image,reference)) and not image['was_resampled']:
        notes.append('Benchmark co-registration is dataset-declared and bounded overlap diagnostics passed; source pixels retained. Residual alignment remains uncertain.')
        return
    if displacement:
        if not settings.enabled('COREGISTER'):
            raise InputError('Visual registration is disabled by configuration.', 'PAIR_MISALIGNMENT')
        shifted = np.full_like(image['array'],np.nan)
        shifted[:,max(0,dy):min(h,h+dy),max(0,dx):min(w,w+dx)] = image['array'][:,max(0,-dy):min(h,h-dy),max(0,-dx):min(w,w-dx)]
        image['array'] = shifted; image['was_coregistered'] = True
        record(image, 'BOUNDED_TRANSLATION', 'Aligned a bounded pixel translation; uncovered borders are nodata.',
               estimated_x_shift=dx, estimated_y_shift=dy, alignment_confidence=score, method=diagnostic['method'],
               alignment_class='GOOD' if displacement<=3 else 'WARNING')
        residual = estimate_pair(reference,image)
        residual_reliable = (residual.get('score') or 0)>=.25 or ((residual.get('score') or 0)>=.05 and residual.get('peak_to_sidelobe_ratio',0)>=12)
        if not residual_reliable or max(abs(v) for v in (residual.get('estimated_shift_pixels') or {'x':999}).values()) > 3:
            notes.append('WARNING: Residual visual alignment verification uncertain; source pixels retained.')
    if displacement > 3:
        notes.append('WARNING: visual registration corrected more than three pixels; review appearance differences carefully.')
    # A pixel alignment never inherits geography from another image.
    image.update(crs=None, transform=None, resolution_m=None, georeferenced=False,
                 visual_only=True, geospatial_measurements_allowed=False)
    notes.append('PIXEL-SPACE TEMPORAL ANALYSIS: bounded visual alignment; no trusted geographic transform or physical area.')


def normalize(images, scenario, notes):
    if len(images) < 2:
        return []
    if scenario != 'CROSS_MODAL_PAIR':
        normalize_bands(images, notes)
    reference = next((i for i in images if i['modality']=='optical'), images[0]) if scenario=='CROSS_MODAL_PAIR' else images[0]
    destination_bytes = int(np.prod(reference['shape'])) * sum(len(i['bands']) for i in images) * 4 * 3
    if destination_bytes > settings.MAX_DECODED_MB * 1024**2:
        raise InputError('Reference-grid derivatives exceed the job memory budget; reduce region size.', 'DECODED_SIZE_EXCEEDED')
    geospatial = all(i['georeferenced'] and i['grid_metadata_valid'] for i in images)
    for image in images:
        if image is reference:
            continue
        try:
            if geospatial:
                warp_to_reference(image,reference)
            else:
                visual_align(image,reference,notes)
        except InputError:
            raise
        except Exception as exc:
            raise InputError('Automatic alignment failed; original inputs remain untouched.', 'PREPROCESSING_FAILED',
                             f'Operation: {"geospatial reprojection" if geospatial else "visual alignment"}; reason: {type(exc).__name__}. Check source metadata.') from exc
    if not geospatial:
        for image in images:
            image.update(crs=None,transform=None,resolution_m=None,georeferenced=False,
                         visual_only=True,geospatial_measurements_allowed=False)
    shared = np.logical_and.reduce([np.isfinite(i['array']).all(0) for i in images])
    fraction = float(shared.mean())
    if fraction < settings.MIN_OVERLAP:
        raise InputError(f'Images have insufficient shared valid spatial overlap ({fraction:.1%}); minimum {settings.MIN_OVERLAP:.0%}.',
                         'NO_SPATIAL_OVERLAP', 'Use observations covering a meaningful common region.')
    # Keep the full reference grid for temporal overlays, mask every nonshared cell.
    # Cross-modal crops use the shared bounding window, with interior holes masked.
    for image in images:
        valid = np.isfinite(image['array']).all(0)
        if np.any(valid & ~shared):
            image['array'] = np.where(shared[None],image['array'],np.nan)
            record(image,'COMMON_VALID_EXTENT','Excluded non-overlapping pixels from every observation.', overlap_fraction=fraction, overlap_pixels=int(shared.sum()))
    if fraction < 1:
        notes.append(f'Spatial overlap: {fraction:.1%}; only shared valid pixels are analyzed.')
    if scenario == 'CROSS_MODAL_PAIR' and fraction < 1:
        ys,xs = np.where(shared); y0,y1,x0,x1 = int(ys.min()),int(ys.max()+1),int(xs.min()),int(xs.max()+1)
        for image in images:
            image['array'] = image['array'][:,y0:y1,x0:x1].copy()
            image['shape'] = [y1-y0,x1-x0]
            image['transform'] = list(Affine(*image['transform'])*Affine.translation(x0,y0))[:6]
            record(image,'CROPPED_COMMON_EXTENT','Cropped optical and SAR to the shared extent.', pixel_window=[x0,y0,x1,y1], original_overlap=fraction,
                   processed_overlap=float(shared[y0:y1,x0:x1].mean()))
    for image in images:
        md = image['raster_metadata']
        md.update(width=image['shape'][1],height=image['shape'][0])
        if image['transform']:
            md['bounds'] = list(array_bounds(*image['shape'],Affine(*image['transform'])))
            md['pixel_resolution'] = [abs(image['transform'][0]),abs(image['transform'][4])]
        else:
            md.update(bounds=None,pixel_resolution=None)
        image['quality'] = assess(image)
    from gateway.alignment import estimate_pair
    alignment = [estimate_pair(a,b) for a,b in zip(images,images[1:])]
    for item in alignment:
        shift=item.get('estimated_shift_pixels')
        item['alignment_class'] = ('POOR' if shift and max(abs(v) for v in shift.values())>10 else
                                   'WARNING' if item.get('warning') else 'GOOD')
        if item.get('warning'):
            notes.append(item['warning'])
    return alignment


def materialize(bundle, directory):
    """Float32 derivatives store already-scaled samples, with identity scale/offset."""
    directory = Path(directory)
    for image in bundle['images']:
        if not image['preprocessing_steps']:
            continue
        directory.mkdir(parents=True,exist_ok=True)
        path = directory / (image['id']+'.tif')
        md = image['raster_metadata']
        try:
            with rasterio.open(path,'w',driver='GTiff',width=image['shape'][1],height=image['shape'][0],
                               count=len(image['bands']),dtype='float32',nodata=np.nan,
                               crs=image['crs'],transform=Affine(*image['transform']) if image['transform'] else None,
                               compress='deflate') as dst:
                dst.write(image['array'])
                dst.update_tags(**md.get('tags',{}))
                dst.update_tags(SATQUERY_SOURCE_SHA256=image['sha256'],SATQUERY_NORMALIZED='1')
                for n,band in enumerate(image['bands'],1):
                    description = md.get('band_descriptions',[])[n-1] or band
                    dst.set_band_description(n,description)
                    dst.update_tags(n,**(md.get('band_tags',[{}]*len(image['bands']))[n-1]))
                colors = md.get('color_interpretation')
                if colors:
                    dst.colorinterp = tuple(ColorInterp[c] for c in colors)
            with rasterio.open(path) as src:
                if list(src.shape) != image['shape'] or src.count != len(image['bands']) or not all(src.descriptions):
                    raise RuntimeError('Derivative verification failed')
                if (str(src.crs) if src.crs else None)!=image['crs'] or image['transform'] and not src.transform.almost_equals(Affine(*image['transform'])):
                    raise RuntimeError('Derivative grid verification failed')
                for n,band in enumerate(image['array'],1):
                    if not np.array_equal(src.read(n),band,equal_nan=True):
                        raise RuntimeError('Derivative samples or nodata changed during persistence')
            image.update(path=str(path),working_path=str(path),normalized_file=path.name,
                         source_file=Path(image['source_path']).name)
            md.update(dtype=['float32']*len(image['bands']),nodata=None,
                      scales=[1.0]*len(image['bands']),offsets=[0.0]*len(image['bands']),
                      band_descriptions=[d or b for d,b in zip(md['band_descriptions'],image['bands'])])
            record(image,'NORMALIZED_DERIVATIVE','Verified internal float32 derivative; source dtype, nodata, scales and tags retained in original metadata.',
                   source_file=Path(image['source_path']).name,normalized_file=path.name,output_dtype='float32',output_nodata='NaN')
        except Exception as exc:
            path.unlink(missing_ok=True)
            raise InputError('Could not write or verify normalized derivative; original uploads remain untouched.', 'PREPROCESSING_FAILED') from exc
