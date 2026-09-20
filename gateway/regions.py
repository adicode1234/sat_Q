"""Pixel AOIs: bounded crops preserve the original coordinate transform."""
from rasterio.transform import Affine
from gateway.errors import InputError


def crop_bundle(bundle,roi):
    box=roi.get('box')
    if not isinstance(box,list) or len(box)!=4 or not all(isinstance(n,int) and not isinstance(n,bool) for n in box):
        raise InputError('ROI must be four integer pixel coordinates')
    x1,y1,x2,y2=box;images=[]
    for image in bundle['images']:
        h,w=image['shape']
        if not (0<=x1<x2<=w and 0<=y1<y2<=h):raise InputError('ROI is outside image bounds')
        cropped={**image,'array':image['array'][:,y1:y2,x1:x2].copy(),'shape':[y2-y1,x2-x1],
                 'roi':box,'parent_image_id':image['id']}
        if image['transform']:
            cropped['transform']=list(Affine(*image['transform'])*Affine.translation(x1,y1))[:6]
            if image.get('crs'):
                from rasterio.transform import array_bounds
                from rasterio.warp import transform_bounds
                bounds = array_bounds(y2-y1, x2-x1, Affine(*cropped['transform']))
                west, south, east, north = transform_bounds(image['crs'], 'EPSG:4326', *bounds)
                cropped['geo_bounds'] = {'west':west,'south':south,'east':east,'north':north,
                                         'center':{'lat':(south+north)/2,'lng':(west+east)/2}}
        from gateway.quality import assess
        cropped['quality']=assess(cropped)
        images.append(cropped)
    return {**bundle,'images':images,'roi':roi,
            'metadata':{**bundle.get('metadata',{}),'geo_bounds':images[0].get('geo_bounds'),
                        'center':(images[0].get('geo_bounds') or {}).get('center')},
            'validation':{**bundle['validation'],'input_quality':min(i['quality']['score'] for i in images)}}


def geographic_box(bundle, bounds):
    """Map a WGS84 rectangle onto one shared, north-up raster grid."""
    import math
    from rasterio.warp import transform_bounds
    if len(bounds) != 4 or not all(math.isfinite(n) for n in bounds):
        raise InputError('Select a valid geographic rectangle.')
    west, south, east, north = bounds
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise InputError('Rectangle must not cross the antimeridian.')
    first = bundle['images'][0]
    if not first.get('crs') or not first.get('transform'):
        raise InputError('Upload georeferenced imagery to analyze a map area. Use image selection for ordinary images.')
    for image in bundle['images'][1:]:
        if any(image.get(k) != first.get(k) for k in ('crs', 'transform', 'shape')):
            raise InputError('Area analysis requires images on the same coordinate grid.')
    transform = Affine(*first['transform'])
    if transform.b or transform.d:
        raise InputError('Rotated rasters must be reprojected before map area selection.')
    left, bottom, right, top = transform_bounds('EPSG:4326', first['crs'], west, south, east, north)
    points = [(~transform) * (x, y) for x in (left, right) for y in (bottom, top)]
    box = [math.floor(min(p[0] for p in points)), math.floor(min(p[1] for p in points)),
           math.ceil(max(p[0] for p in points)), math.ceil(max(p[1] for p in points))]
    h, w = first['shape']
    if box[0] < 0 or box[1] < 0 or box[2] > w or box[3] > h:
        raise InputError('Selected area is outside the source image. Draw inside its footprint.')
    return box
