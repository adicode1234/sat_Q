"""Create a metadata-tagged TIFF copy for the unchanged upload UI. Never infer scale."""
import argparse
from pathlib import Path
import numpy as np
import rasterio
from rasterio.shutil import copy

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True);p.add_argument('--output',required=True)
    p.add_argument('--bands',required=True,help='Comma-separated physical band names in file order')
    p.add_argument('--scale',required=True,type=float,help='Source-documented reflectance scale; never guess this value')
    p.add_argument('--offset',type=float,default=0)
    args=p.parse_args();source=Path(args.input).resolve();target=Path(args.output).resolve();bands=args.bands.split(',')
    if target.exists() or source==target:raise ValueError('Output must be a new file; original imagery is never overwritten')
    if not np.isfinite(args.scale) or args.scale<=0 or not np.isfinite(args.offset):raise ValueError('Invalid scale/offset')
    with rasterio.open(source) as src:
        if src.count!=len(bands) or len(set(bands))!=len(bands):raise ValueError('Band names must be unique and match channel count')
        if any(s!=1 for s in src.scales) or any(o!=0 for o in src.offsets):raise ValueError('Input already has raster scale/offset; use those directly')
    target.parent.mkdir(parents=True,exist_ok=True)
    copy(source,target,driver='GTiff')
    with rasterio.open(target,'r+') as dst:
        dst.scales=[args.scale]*len(bands);dst.offsets=[args.offset]*len(bands)
        for n,b in enumerate(bands,1):dst.set_band_description(n,b.strip())
    print(target)
if __name__=='__main__':main()
