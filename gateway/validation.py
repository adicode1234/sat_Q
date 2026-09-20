"""Inspect, normalize, verify; never infer missing geography or calibration."""
from pathlib import Path
from datetime import date
import hashlib
import re
import numpy as np
import rasterio
from PIL import Image
from rasterio.transform import Affine
from rasterio.warp import transform_bounds
from gateway.errors import InputError, FailureCode
from gateway.quality import assess, suggest_modality
from gateway import settings
from gateway.normalization import initialize, band_name, normalize

MAX_PIXELS = 16_000_000

KNOWN_LOCATIONS = {
    'kolkata': {
        'west': 88.2500, 'south': 22.4500, 'east': 88.4800, 'north': 22.6800,
        'center': {'lat': 22.5726, 'lng': 88.3639},
        'location_name': 'Kolkata & Hooghly River Basin (West Bengal)'
    },
    'calcutta': {
        'west': 88.2500, 'south': 22.4500, 'east': 88.4800, 'north': 22.6800,
        'center': {'lat': 22.5726, 'lng': 88.3639},
        'location_name': 'Kolkata & Hooghly River Basin (West Bengal)'
    },
    'howrah': {
        'west': 88.2000, 'south': 22.5200, 'east': 88.3300, 'north': 22.6600,
        'center': {'lat': 22.5958, 'lng': 88.2636},
        'location_name': 'Howrah & Hooghly Riverfront (West Bengal)'
    },
    'delhi': {
        'west': 77.1000, 'south': 28.5000, 'east': 77.3500, 'north': 28.7500,
        'center': {'lat': 28.6139, 'lng': 77.2090},
        'location_name': 'New Delhi (National Capital Region, Yamuna)'
    },
    'mumbai': {
        'west': 72.7500, 'south': 18.8800, 'east': 72.9800, 'north': 19.2500,
        'center': {'lat': 19.0760, 'lng': 72.8777},
        'location_name': 'Mumbai Urban Coastal Bay (Maharashtra)'
    },
    'bombay': {
        'west': 72.7500, 'south': 18.8800, 'east': 72.9800, 'north': 19.2500,
        'center': {'lat': 19.0760, 'lng': 72.8777},
        'location_name': 'Mumbai Urban Coastal Bay (Maharashtra)'
    },
    'surat': {
        'west': 72.7600, 'south': 21.1200, 'east': 72.9000, 'north': 21.2400,
        'center': {'lat': 21.1800, 'lng': 72.8300},
        'location_name': 'Tapi River Basin & Surat Estuary (Gujarat)'
    },
    'bengaluru': {
        'west': 77.5000, 'south': 12.8500, 'east': 77.7200, 'north': 13.0800,
        'center': {'lat': 12.9716, 'lng': 77.5946},
        'location_name': 'Bengaluru Tech & Space Corridor (Karnataka)'
    },
    'bangalore': {
        'west': 77.5000, 'south': 12.8500, 'east': 77.7200, 'north': 13.0800,
        'center': {'lat': 12.9716, 'lng': 77.5946},
        'location_name': 'Bengaluru Tech & Space Corridor (Karnataka)'
    },
    'chennai': {
        'west': 80.1800, 'south': 12.9800, 'east': 80.3200, 'north': 13.1800,
        'center': {'lat': 13.0827, 'lng': 80.2707},
        'location_name': 'Chennai Coastal Bay & Marina (Tamil Nadu)'
    },
    'hyderabad': {
        'west': 78.3500, 'south': 17.2800, 'east': 78.5800, 'north': 17.4800,
        'center': {'lat': 17.3850, 'lng': 78.4867},
        'location_name': 'Hyderabad & Musi Basin (Telangana)'
    },
    'ahmedabad': {
        'west': 72.4800, 'south': 22.9500, 'east': 72.6800, 'north': 23.1200,
        'center': {'lat': 23.0225, 'lng': 72.5714},
        'location_name': 'Ahmedabad Sabarmati Riverfront (Gujarat)'
    },
    'jaipur': {
        'west': 75.7000, 'south': 26.8200, 'east': 75.8800, 'north': 27.0200,
        'center': {'lat': 26.9124, 'lng': 75.7873},
        'location_name': 'Jaipur Pink City & Aravalli Basin (Rajasthan)'
    },
    'pune': {
        'west': 73.7600, 'south': 18.4200, 'east': 73.9600, 'north': 18.6200,
        'center': {'lat': 18.5204, 'lng': 73.8567},
        'location_name': 'Pune Mula-Mutha River Valley (Maharashtra)'
    },
    'lucknow': {
        'west': 80.8500, 'south': 26.7500, 'east': 81.0500, 'north': 26.9500,
        'center': {'lat': 26.8467, 'lng': 80.9462},
        'location_name': 'Lucknow Gomti River Corridor (Uttar Pradesh)'
    },
    'varanasi': {
        'west': 82.9000, 'south': 25.2500, 'east': 83.0500, 'north': 25.3800,
        'center': {'lat': 25.3176, 'lng': 82.9739},
        'location_name': 'Varanasi Ganga Ghats Basin (Uttar Pradesh)'
    },
    'patna': {
        'west': 85.0500, 'south': 25.5400, 'east': 85.2200, 'north': 25.6800,
        'center': {'lat': 25.6093, 'lng': 85.1376},
        'location_name': 'Patna Ganga River Basin (Bihar)'
    },
    'bhopal': {
        'west': 77.3300, 'south': 23.1800, 'east': 77.4900, 'north': 23.3400,
        'center': {'lat': 23.2599, 'lng': 77.4126},
        'location_name': 'Bhopal Upper Lake & Urban Zone (Madhya Pradesh)'
    },
    'indore': {
        'west': 75.7800, 'south': 22.6500, 'east': 75.9400, 'north': 22.7900,
        'center': {'lat': 22.7196, 'lng': 75.8577},
        'location_name': 'Indore Urban Region (Madhya Pradesh)'
    },
    'chandigarh': {
        'west': 76.7000, 'south': 30.6800, 'east': 76.8600, 'north': 30.8000,
        'center': {'lat': 30.7333, 'lng': 76.7794},
        'location_name': 'Chandigarh Capital Region (Punjab/Haryana)'
    },
    'bhubaneswar': {
        'west': 85.7400, 'south': 20.2200, 'east': 85.9000, 'north': 20.3700,
        'center': {'lat': 20.2961, 'lng': 85.8245},
        'location_name': 'Bhubaneswar Smart City (Odisha)'
    },
    'guwahati': {
        'west': 91.6400, 'south': 26.0800, 'east': 91.8400, 'north': 26.2200,
        'center': {'lat': 26.1445, 'lng': 91.7362},
        'location_name': 'Guwahati Brahmaputra Valley (Assam)'
    },
    'sundarbans': {
        'west': 88.8000, 'south': 21.6000, 'east': 89.6000, 'north': 22.3000,
        'center': {'lat': 21.9497, 'lng': 89.1833},
        'location_name': 'Sundarbans Mangrove Delta & Tidal Forest'
    },
    'thar': {
        'west': 70.7000, 'south': 26.7000, 'east': 71.2000, 'north': 27.2000,
        'center': {'lat': 26.9157, 'lng': 70.9083},
        'location_name': 'Thar Desert Radar Calibration Field (Jaisalmer)'
    },
    'ladakh': {
        'west': 77.4500, 'south': 34.0500, 'east': 77.7000, 'north': 34.2500,
        'center': {'lat': 34.1526, 'lng': 77.5771},
        'location_name': 'Leh Ladakh High-Altitude Plateau (Himalayas)'
    },
    'leh': {
        'west': 77.4500, 'south': 34.0500, 'east': 77.7000, 'north': 34.2500,
        'center': {'lat': 34.1526, 'lng': 77.5771},
        'location_name': 'Leh Ladakh High-Altitude Plateau (Himalayas)'
    },
    'goa': {
        'west': 73.7000, 'south': 15.1000, 'east': 74.2500, 'north': 15.5500,
        'center': {'lat': 15.2993, 'lng': 74.1240},
        'location_name': 'Goa Coastal Estuaries & Mandovi River'
    },
    'kerala': {
        'west': 76.1500, 'south': 9.8000, 'east': 76.3800, 'north': 10.0500,
        'center': {'lat': 9.9312, 'lng': 76.2673},
        'location_name': 'Kochi & Vembanad Backwaters (Kerala)'
    },
    'kochi': {
        'west': 76.1500, 'south': 9.8000, 'east': 76.3800, 'north': 10.0500,
        'center': {'lat': 9.9312, 'lng': 76.2673},
        'location_name': 'Kochi & Vembanad Backwaters (Kerala)'
    },
    'hassan': {
        'west': 76.3600, 'south': 13.0700, 'east': 76.4300, 'north': 13.1300,
        'center': {'lat': 13.1009, 'lng': 76.3955},
        'location_name': 'ISRO Master Control Facility (Hassan, Karnataka)'
    },
    'cairo': {
        'west': 31.0500, 'south': 29.9000, 'east': 31.2500, 'north': 30.1000,
        'center': {'lat': 29.9792, 'lng': 31.1342},
        'location_name': 'Giza Plateau & Nile River Valley (Egypt)'
    },
    'dubai': {
        'west': 55.1500, 'south': 25.0500, 'east': 55.3800, 'north': 25.3000,
        'center': {'lat': 25.2048, 'lng': 55.2708},
        'location_name': 'Dubai Palm & Coastal Gulf (UAE)'
    },
    'london': {
        'west': -0.2500, 'south': 51.4000, 'east': 0.0500, 'north': 51.6000,
        'center': {'lat': 51.5074, 'lng': -0.1278},
        'location_name': 'London Thames River Basin (UK)'
    },
    'paris': {
        'west': 2.2200, 'south': 48.7800, 'east': 2.4500, 'north': 48.9500,
        'center': {'lat': 48.8566, 'lng': 2.3522},
        'location_name': 'Paris Seine River Basin (France)'
    },
    'new york': {
        'west': -74.1500, 'south': 40.6000, 'east': -73.8500, 'north': 40.8500,
        'center': {'lat': 40.7128, 'lng': -74.0060},
        'location_name': 'New York Harbor & Hudson Estuary (USA)'
    },
    'tokyo': {
        'west': 139.5500, 'south': 35.5500, 'east': 139.8500, 'north': 35.8000,
        'center': {'lat': 35.6762, 'lng': 139.6503},
        'location_name': 'Tokyo Bay Urban Coastal Zone (Japan)'
    },
    'singapore': {
        'west': 103.6500, 'south': 1.2200, 'east': 103.9800, 'north': 1.4800,
        'center': {'lat': 1.3521, 'lng': 103.8198},
        'location_name': 'Singapore Island & Marina Bay'
    },
    'sydney': {
        'west': 151.1000, 'south': -33.9500, 'east': 151.3000, 'north': -33.7800,
        'center': {'lat': -33.8688, 'lng': 151.2093},
        'location_name': 'Sydney Port Jackson Harbor (Australia)'
    }
}

def resolve_query_location(text: str):
    if not text:
        return None
    coord_m = re.search(r'(-?\d{1,2}\.\d+)[,\s]+(-?\d{1,3}\.\d+)', str(text))
    if coord_m:
        lat = float(coord_m.group(1))
        lng = float(coord_m.group(2))
        if -90 <= lat <= 90 and -180 <= lng <= 180:
            span = 0.04
            return {
                'west': round(lng - span, 4), 'south': round(lat - span, 4),
                'east': round(lng + span, 4), 'north': round(lat + span, 4),
                'center': {'lat': round(lat, 4), 'lng': round(lng, 4)},
                'location_name': f'Target Coordinates ({lat:.4f}° N, {lng:.4f}° E)'
            }
    lower = str(text).lower()
    for key, loc in KNOWN_LOCATIONS.items():
        if key in lower:
            return loc
    return None

def read_image(path, image_id, options):
    path = Path(path)
    modality = options.get('modality', 'optical')
    if modality not in ('optical', 'SAR'):
        raise ValueError('Modality must be optical or SAR')
    suffix = path.suffix.lower()
    crs, transform, resolution = None, None, None
    metadata = {}; encoded_date = None
    settings.check_size(path.stat().st_size)
    with path.open('rb') as handle:
        signature = handle.read(16)
    geo_bounds = None
    if suffix in ('.tif', '.tiff'):
        if signature[:4] not in ((b'II*' + b'\x00'),(b'MM' + b'\x00*'),(b'II+' + b'\x00'),(b'MM' + b'\x00+')):
            raise InputError('Invalid TIFF signature or unreadable raster')
        with rasterio.open(path) as src:
            if src.width * src.height > MAX_PIXELS or src.count > 16:
                raise ValueError('Image limit: 16 million pixels and 16 bands')
            arr = src.read(masked=True).astype('float32').filled(np.nan)
            scales, offsets = list(src.scales), list(src.offsets)
            arr = arr * np.asarray(scales,dtype='float32')[:,None,None] + np.asarray(offsets,dtype='float32')[:,None,None]
            crs = str(src.crs) if src.crs else None
            transform = list(src.transform)[:6] if src.transform != Affine.identity() else None
            resolution = abs(src.res[0])*src.crs.linear_units_factor[1] if src.crs and src.crs.is_projected else None
            bands = options.get('bands') or [b.lower() if b else f'band_{i+1}' for i,b in enumerate(src.descriptions)]
            tags = src.tags()
            for key in ('ACQUISITION_DATE','acquisition_date','DATE_ACQUIRED','SENSING_TIME','TIFFTAG_DATETIME'):
                value = tags.get(key)
                if value:
                    try: encoded_date = date.fromisoformat(value[:10].replace(':','-')).isoformat()
                    except ValueError: pass
                    if encoded_date: break
            if crs and transform:
                try:
                    wgs = transform_bounds(src.crs, 'EPSG:4326', *src.bounds)
                    if -180.0 <= wgs[0] <= 180.0 and -90.0 <= wgs[1] <= 90.0 and -180.0 <= wgs[2] <= 180.0 and -90.0 <= wgs[3] <= 90.0:
                        geo_bounds = {
                            'west': float(wgs[0]), 'south': float(wgs[1]),
                            'east': float(wgs[2]), 'north': float(wgs[3]),
                            'center': {'lat': float((wgs[1] + wgs[3]) / 2), 'lng': float((wgs[0] + wgs[2]) / 2)}
                        }
                except Exception:
                    geo_bounds = None
            metadata = {'format':src.driver,'width':src.width,'height':src.height,'band_count':src.count,
                        'band_descriptions':list(src.descriptions),'dtype':list(src.dtypes),
                        'nodata':float(src.nodata) if src.nodata is not None and np.isfinite(src.nodata) else None,
                        'bounds':list(src.bounds) if crs and transform else None,'pixel_resolution':list(src.res) if transform else None,
                        'geo_bounds': geo_bounds,
                        'scales':scales,'offsets':offsets,'scale_offset_applied':True,'tags':tags,
                        'band_tags':[src.tags(n) for n in range(1,src.count+1)],
                        'color_interpretation':[c.name for c in src.colorinterp], 'encoded_acquisition_date':encoded_date}
    elif suffix in ('.png', '.jpg', '.jpeg'):
        with Image.open(path) as src:
            if src.format not in ('PNG','JPEG') or (suffix=='.png') != (src.format=='PNG'):
                raise InputError('Image signature does not match its filename format',FailureCode.UNSUPPORTED_FORMAT)
            if src.width * src.height > MAX_PIXELS:
                raise ValueError('Image exceeds 16 million pixels')
            arr = np.asarray(src.convert('RGB'), dtype=np.float32).transpose(2,0,1) / 255
            metadata = {'format':src.format,'width':src.width,'height':src.height,'band_count':3,
                        'dtype':['uint8']*3,'nodata':None,'bounds':None,'pixel_resolution':None,
                        'geo_bounds': None,
                        'tags':{},'band_descriptions':['red','green','blue'],'scales':[1/255]*3,'offsets':[0]*3,'scale_offset_applied':True}
        bands = ['red', 'green', 'blue']
    else:
        raise InputError('Supported formats: GeoTIFF/TIFF, PNG, JPG and JPEG', FailureCode.UNSUPPORTED_FORMAT)
    bands = [band_name(b, {**metadata.get('tags',{}),'declared_sensor':options.get('sensor','')}) for b in bands]
    if len(bands) != arr.shape[0] or len(set(bands)) != len(bands):
        raise ValueError('Band names must be unique and match channel count')
    if not np.isfinite(arr).any():
        raise ValueError('Image contains no valid pixels')
    acquisition_date = options.get('date') or encoded_date
    if acquisition_date: date.fromisoformat(acquisition_date)
    units = options.get('sar_units','unknown')
    if units not in ('unknown','db','linear'): raise InputError('SAR units must be unknown, db or linear')
    if modality == 'SAR' and units == 'unknown':
        finite = arr[np.isfinite(arr)]
        if finite.size > 0 and float(finite.min()) < 0 and float(finite.max()) <= 35.0:
            units = 'db'
    demo_root = Path(__file__).resolve().parents[1]/'data/demo'
    domain = ('synthetic_demo' if path.resolve().is_relative_to(demo_root) else
              'benchmark' if options.get('benchmark_source') else 'operational_geospatial' if crs and transform else 'unreferenced_tiff')
    with path.open('rb') as handle:
        digest=hashlib.file_digest(handle,'sha256').hexdigest()
    if not geo_bounds:
        geo_bounds = options.get('geo_bounds')
    image = {'id': image_id, 'modality': modality, 'bands': bands, 'path': str(path),
            'filename':options.get('original_filename') or path.name,'sha256':digest,
            'source_type':domain,'georeferenced':bool(crs and transform), 'raster_metadata':metadata,
            'geo_bounds': geo_bounds,
            'crs': crs, 'transform': transform, 'resolution_m': resolution,
            'shape': list(arr.shape[1:]), 'date': acquisition_date, 'time_index': options.get('time_index'),
            'date_source':'user_declared' if options.get('date') else 'raster_metadata' if encoded_date else None,
            'sar_units': units,'calibration_state':'user_declared_calibrated' if options.get('sar_units') in ('db','linear') else ('inferred_calibrated_db' if units=='db' else 'unknown'),
            'coregistered':bool(options.get('coregistered')),
            'benchmark_source': options.get('benchmark_source'), 'array': arr}
    from gateway.radiometry import prepare
    prepare(image,options)
    image['quality'] = assess(image)
    image['suggested_modality'] = suggest_modality(image)
    initialize(image)
    if image['radiometry'].get('reflectance_conversion'):
        from gateway.normalization import record
        record(image,'REFLECTANCE_CONVERSION','Converted samples using declared scale/offset; original upload preserved.',**image['radiometry']['reflectance_conversion'])
    if image['modality']=='SAR' and units=='unknown':
        image['warnings'].append('Raw SAR DN cannot be calibrated from image brightness alone. Supply calibrated power, its units and polarization metadata.')
    return image

def validate(paths, options, scenario, query=''):
    settings.check_count(scenario,len(paths))
    if len(options) != len(paths):
        raise InputError('One options object is required per image')
    estimated = 0
    for path in paths:
        settings.check_size(Path(path).stat().st_size)
        try:
            if Path(path).suffix.lower() in ('.tif','.tiff'):
                with rasterio.open(path) as src:
                    estimated += src.width * src.height * src.count * 4 * 3
            else:
                with Image.open(path) as src:
                    estimated += src.width * src.height * 3 * 4 * 3
        except Exception as exc:
            raise InputError('Unreadable image or invalid file signature.', 'UNREADABLE_IMAGE') from exc
    if estimated > settings.MAX_DECODED_MB * 1024**2:
        raise InputError('Decoded imagery exceeds the bounded job memory budget; use a smaller region or fewer bands.', 'DECODED_SIZE_EXCEEDED')
    try:
        images = [read_image(p, f'img{i+1}', o) for i,(p,o) in enumerate(zip(paths,options))]
    except InputError:
        raise
    except Exception as exc:
        raise InputError('Image metadata or content is invalid: '+str(exc), 'INVALID_IMAGE') from exc
    notes = []
    for image in images:
        suggestion = image['suggested_modality']
        suffix = Path(image['path']).suffix.lower()
        is_rgb_file = suffix in ('.png', '.jpg', '.jpeg') or (len(image.get('bands', [])) >= 3 and all(b in image.get('bands', []) for b in ('red', 'green', 'blue')))
        if image['modality'] == 'SAR' and suggestion in ('OPTICAL', 'MULTISPECTRAL', 'NDVI/SPECTRAL_INDEX'):
            if scenario == 'CROSS_MODAL_PAIR':
                notes.append('SAR preview modality confirmed for cross-modal analysis.')
            elif is_rgb_file:
                image['modality'] = 'optical'
                notes.append('Auto-adjusted modality from SAR to OPTICAL based on 3-channel RGB image structure.')
            else:
                raise InputError('POSSIBLE MODALITY MISMATCH: selected SAR but metadata suggests ' + suggestion,
                                 FailureCode.MODALITY_MISMATCH, 'Confirm modality; spectral indices are not SAR.')
        elif image['modality'] == 'optical' and suggestion == 'SAR':
            if any(s in image.get('bands', []) for s in ('vv', 'vh', 'hh', 'hv')) and scenario != 'CROSS_MODAL_PAIR':
                image['modality'] = 'SAR'
                notes.append('Auto-adjusted modality from OPTICAL to SAR based on radar polarization bands.')
            else:
                raise InputError('POSSIBLE MODALITY MISMATCH: radar-like bands selected as optical', FailureCode.MODALITY_MISMATCH)
        notes.extend(image['quality']['warnings'])
        notes.extend(image['warnings'])
    if scenario == 'CROSS_MODAL_PAIR':
        if {i['modality'] for i in images} != {'optical','SAR'}:
            raise InputError('Cross-modal input requires one optical and one SAR image', FailureCode.MODALITY_MISMATCH)
    elif len(images)>1:
        if len({i['modality'] for i in images}) != 1:
            raise InputError('INCOMPATIBLE FOR TEMPORAL CHANGE: before/after modalities differ (Optical / SAR).',
                             FailureCode.MODALITY_MISMATCH,'Suggested mode: Optical + SAR (CROSS_MODAL_PAIR).')
        for a,b in zip(images,images[1:]):
            if a['date'] and b['date']:
                if a['date'] >= b['date']:
                    raise InputError('Temporal dates must be earlier image first', 'TEMPORAL_ORDER_INVALID')
            elif scenario=='MULTI_DATE':
                raise InputError('Multi-date images need increasing acquisition dates', 'TEMPORAL_DATES_REQUIRED')
            else:
                notes.append('Before/after order is user-declared by upload slots; acquisition dates unavailable.')
        if images[0]['modality']=='SAR' and len({i['sar_units'] for i in images}) > 1:
            raise InputError('Temporal SAR observations use different unit states; absolute differences would be misleading.',
                             'SAR_UNIT_MISMATCH','Supply consistent known units or compare each observation separately.')
    if len(images)>8:
        notes.append('Large observation sequence: preprocessing and inference may take longer.')
    alignment = normalize(images,scenario,notes)
    unavailable = []
    from verification.engine import INDEX_BANDS
    for name,required in INDEX_BANDS.items():
        if name.lower() in query.lower() and any(not all(b in i['bands'] for b in required) for i in images):
            unavailable.append(name)
            notes.append(f'{name} unavailable: every observation requires {" + ".join(required)}. Other visual tasks remain available.')
    steps = [step for image in images for step in image['preprocessing_steps']]
    notes = list(dict.fromkeys(notes))
    state = 'READY_WITH_PREPROCESSING' if steps else 'READY_WITH_LIMITATIONS' if notes else 'READY'
    primary_geo_bounds = images[0].get('geo_bounds')
    return {'scenario':scenario, 'images':images,
            'metadata':{'crs':images[0]['crs'],'resolution_m':images[0]['resolution_m'],
                        'geo_bounds':primary_geo_bounds,
                        'center':primary_geo_bounds.get('center') if primary_geo_bounds else None,
                        'acquisition_dates':[i['date'] for i in images]},
            'validation_status':state,'validation_notes':'; '.join(notes) or 'Formats, bands and spatial grids verified',
            'validation':{'status':state,'alignment':alignment,'preprocessing_steps':steps,
                          'issues_detected':list(dict.fromkeys(code for s in steps for code in s.get('issues_detected',[s['code']]))),
                          'actions_taken':steps,'warnings':notes,'blocking_errors':[],
                          'has_limitations':bool(notes),
                          'unavailable_tasks':unavailable,
                          'capabilities':{'visual_analysis':True,'pixel_measurements':True,
                                          'physical_area':all(i['geospatial_measurements_allowed'] for i in images)},
                          'reasons':[{'code':'INPUT_LIMITATION','message':n} for n in notes],
                          'input_quality':min(i['quality']['score'] for i in images)}}

def public_contract(bundle):
    return {**bundle,'images':[{k:v for k,v in i.items() if k not in ('array','path','source_path','working_path')} for i in bundle['images']]}

def rgb(image):
    a=image['array']; bands=image['bands']
    if all(b in bands for b in ('red','green','blue')):
        a=a[[bands.index(b) for b in ('red','green','blue')]]
    else:
        a=np.repeat(a[:1],3,axis=0)
    if image.get('source_type')!='synthetic_demo' and image.get('raster_metadata',{}).get('format') in ('PNG','JPEG'):
        return (np.clip(np.nan_to_num(a),0,1).transpose(1,2,0)*255).astype('uint8')
    if image.get('radiometry',{}).get('reflectance_scale_known') and image.get('source_type')!='synthetic_demo':
        return (np.clip(np.nan_to_num(a)/.3,0,1).transpose(1,2,0)*255).astype('uint8')
    out=[]
    for band in a:
        finite=band[np.isfinite(band)]
        lo,hi=np.percentile(finite,[2,98]) if finite.size else (0,1)
        out.append(np.clip((np.nan_to_num(band,nan=float(lo))-lo)/max(float(hi-lo),1e-6),0,1))
    return (np.stack(out).transpose(1,2,0)*255).astype('uint8')
