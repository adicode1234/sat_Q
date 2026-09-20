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
        from gateway.quality import assess
        cropped['quality']=assess(cropped)
        images.append(cropped)
    return {**bundle,'images':images,'roi':roi,
            'validation':{**bundle['validation'],'input_quality':min(i['quality']['score'] for i in images)}}
