"""Generate explicitly synthetic, georeferenced test fixtures, never benchmark data."""
import json
from pathlib import Path
import numpy as np
import rasterio
from rasterio.transform import from_origin
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
PALETTE=np.array([[.07,.17,.23,.025,.015],[.12,.27,.09,.65,.19],[.37,.35,.32,.30,.46],[.32,.24,.13,.27,.31]],dtype='float32')

def scene(seed=41,size=256):
    rng=np.random.default_rng(seed);y,x=np.mgrid[:size,:size];labels=np.ones((size,size),dtype=int)
    labels[(x>size*.58)&(y>size*.28)&(y<size*.83)]=2
    labels[(x<size*.32)&(y>size*.66)]=3
    labels[np.abs(x-(size*.42+np.sin(y/size*7)*size*.1))<size*.065]=0
    a=PALETTE[labels].transpose(2,0,1)+rng.normal(0,.015,(5,size,size))
    return np.clip(a,0,1).astype('float32'),labels

def write_tif(path,array,bands):
    with rasterio.open(path,'w',driver='GTiff',height=array.shape[1],width=array.shape[2],count=len(bands),dtype='float32',crs='EPSG:32643',transform=from_origin(650000,1450000,10,10),nodata=-9999) as dst:
        dst.write(array)
        for i,name in enumerate(bands,1):dst.set_band_description(i,name)

def main():
    folder=ROOT/'data/demo';folder.mkdir(parents=True,exist_ok=True)
    a,labels=scene();b=a.copy();b[:,55:120,155:220]=PALETTE[0][:,None,None]
    write_tif(folder/'optical_before.tif',a,['red','green','blue','nir','swir'])
    write_tif(folder/'optical_after.tif',b,['red','green','blue','nir','swir'])
    rng=np.random.default_rng(99);sar=np.where(labels==0,-22,-9)+rng.normal(0,1.5,labels.shape)
    sar[30:215,140:250]=-23
    write_tif(folder/'sar.tif',sar.astype('float32')[None],['vv'])
    from gateway.validation import read_image,rgb
    for name in ['optical_before','optical_after','sar']:
        Image.fromarray(rgb(read_image(folder/f'{name}.tif',name,{'modality':'SAR' if name=='sar' else 'optical'}))).save(folder/f'{name}.png')
    optical={'modality':'optical','date':'2024-01-01'}
    demos=[
      {'id':'vqa','title':'Survey the scene','label':'Single image · VQA','scenario':'SINGLE','query':'What land cover is visible in this satellite image?','paths':['data/demo/optical_before.tif'],'options':[optical]},
      {'id':'grounding','title':'Locate surface water','label':'Single image · Grounding','scenario':'SINGLE','query':'Highlight water in this image.','paths':['data/demo/optical_before.tif'],'options':[optical]},
      {'id':'change','title':'Inspect change over time','label':'Bi-temporal · Change VQA','scenario':'BITEMPORAL_PAIR','query':'What changed between these two acquisitions?','paths':['data/demo/optical_before.tif','data/demo/optical_after.tif'],'options':[optical,{'modality':'optical','date':'2024-07-01'}]},
      {'id':'fusion','title':'Cross-check optical + SAR','label':'Cross-modal · Joint analysis','scenario':'CROSS_MODAL_PAIR','query':'Compare water evidence in optical and SAR imagery.','paths':['data/demo/optical_before.tif','data/demo/sar.tif'],'options':[optical,{'modality':'SAR','sar_units':'db','date':'2024-01-01'}]}
    ]
    for d in demos:d['provenance']='Synthetic georeferenced fixture; not a real observation or public benchmark'
    (folder/'manifest.json').write_text(json.dumps(demos,indent=2))
    print('Created four synthetic demo scenarios')
if __name__=='__main__':main()
