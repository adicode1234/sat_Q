"""Re-run the same image/query against base and adapted RGB weights."""
import json
from pathlib import Path
from gateway.validation import read_image
from models.features import pixel_predictions,LABELS
def main():
    root=Path(__file__).resolve().parents[1];image=read_image(root/'data/demo/optical_before.tif','img1',{})
    out={'query':'What land cover is visible in this image?','image':'data/demo/optical_before.tif','scope':'synthetic demo, not real benchmark improvement'}
    for name in ['base','adapter']:
        mask,p,_=pixel_predictions(image,root/f'models/checkpoints/rgb_{name}.npz')
        out[name]={k:float((mask==i).mean()) for i,k in enumerate(LABELS)}
    (root/'training/comparison.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
