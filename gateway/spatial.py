"""Lossless pixel masks, geographic exports and measured region area."""
import base64
import zlib
import numpy as np
from rasterio.features import shapes
from rasterio.transform import Affine
from rasterio.warp import transform_geom


def pack_mask(mask):
    mask=np.asarray(mask,dtype='uint8')
    return {'encoding':'zlib-base64-uint8','shape':list(mask.shape),
            'data':base64.b64encode(zlib.compress(mask.tobytes())).decode('ascii')}


def unpack_mask(packed):
    shape=packed['shape']
    if len(shape)!=2 or not all(isinstance(n,int) and 0<n for n in shape) or np.prod(shape)>16_000_000:
        raise ValueError('Invalid mask dimensions')
    count=int(np.prod(shape));decoder=zlib.decompressobj()
    raw=decoder.decompress(base64.b64decode(packed['data'],validate=True),count+1)
    if len(raw)!=count or not decoder.eof:raise ValueError('Invalid or oversized mask payload')
    return np.frombuffer(raw,dtype='uint8').reshape(shape).astype(bool)


def heatmap(values, image_id, semantics):
    values=np.asarray(values);stride=max(1,int(np.ceil(max(values.shape)/192)))
    sampled=values[::stride,::stride]
    return {'type':'heatmap','image_id':image_id,'width':values.shape[1],'height':values.shape[0],
            'data':[[float(v) if np.isfinite(v) else None for v in row] for row in sampled],
            'semantics':semantics,'calibrated':False,'display_stride':stride}


def polygon_area(geometry):
    def ring_area(ring):
        points=np.asarray(ring,dtype=float)
        # Translation prevents cancellation for small polygons in large coordinates.
        points=points-points[0]
        return abs(float(np.sum(points[:-1,0]*points[1:,1]-points[1:,0]*points[:-1,1])))*.5
    polygons=[geometry['coordinates']] if geometry['type']=='Polygon' else geometry['coordinates']
    return sum(max(0,ring_area(p[0])-sum(ring_area(r) for r in p[1:])) for p in polygons)


def region_features(image, mask, label='selected region', max_features=5000):
    if not image.get('georeferenced') or not image.get('geospatial_measurements_allowed', True):
        return {'type':'FeatureCollection','features':[], 'status':'UNAVAILABLE',
                'reason':'GEOSPATIAL_METADATA_UNVERIFIED: trustworthy CRS/geotransform required; pixel measurements remain available.'}
    affine=Affine(*image['transform'])
    features=[];total=0.0
    for geometry,value in shapes(np.asarray(mask,dtype='uint8'),mask=np.asarray(mask,dtype=bool),transform=affine):
        # Equal-area WGS84 projection; no degree-squared or naive GSD arithmetic.
        equal_area=transform_geom(image['crs'],'EPSG:6933',geometry,precision=-1)
        area=polygon_area(equal_area);total+=area
        geographic=transform_geom(image['crs'],'EPSG:4326',geometry,precision=9)
        features.append({'type':'Feature','geometry':geographic,'properties':{'image_id':image['id'],'label':label,
                         'area_m2':area,'area_ha':area/10000,'area_km2':area/1e6,'source_crs':image['crs'],
                         'source_type':image.get('source_type'),'method':'Raster boundaries transformed to EPSG:6933 equal-area; approximate transformed edge geometry.'}})
        if len(features)>max_features:
            return {'type':'FeatureCollection','features':[], 'status':'UNAVAILABLE',
                    'reason':'Too many disconnected regions for bounded GeoJSON export; use the full-resolution mask raster.'}
    return {'type':'FeatureCollection','features':features,'status':'READY','area_m2':total,
            'area_ha':total/10000,'area_km2':total/1e6,'pixel_count':int(np.asarray(mask,dtype=bool).sum()),
            'method':'EPSG:6933 equal-area polygon measurement; synthetic grids remain synthetic.'}


def spatial_products(bundle, outputs):
    by_id={i['id']:i for i in bundle['images']};products=[]
    for out in outputs:
        overlay=out.get('overlay')
        if not overlay:continue
        image=by_id[overlay['image_id']]
        if out.get('raw_mask'):
            mask=unpack_mask(out['raw_mask'])
            products.append({'label':overlay.get('label','Candidate region'),'image_id':image['id'],
                             'raw_mask':out['raw_mask'],'pixel_count':int(mask.sum()),
                             'geojson':region_features(image,mask,overlay.get('label','Candidate region'))})
        elif overlay['type']=='bbox':
            for n,box in enumerate(overlay['data']):
                x1,y1,x2,y2=box['box'];mask=np.zeros(image['shape'],dtype=bool);mask[y1:y2,x1:x2]=True
                products.append({'label':box['label'],'image_id':image['id'],'box_index':n,
                                 'pixel_count':int(mask.sum()),'geojson':region_features(image,mask,box['label']),
                                 'limitation':'Bounding-box area includes background; not segmented object area.'})
    return products
