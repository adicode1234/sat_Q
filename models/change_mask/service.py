"""Optional standalone change-mask head service using the same fallback algorithm."""
from fastapi import FastAPI
from models.service import run as run_specialist
from models.change_mask.model import run
from gateway.validation import read_image
from pathlib import Path
from fastapi import HTTPException
app=FastAPI(title='SatQuery change-mask head')
ROOT=Path(__file__).resolve().parents[2]
@app.get('/health')
def health():return {'status':'ok','mode':'deterministic_change_mask_fallback'}
@app.post('/run')
def mask(payload:dict):
    images=[]
    for image in payload['bundle']['images']:
        path=Path(image['path']).resolve()
        if not path.is_relative_to(ROOT/'data'):raise HTTPException(422,'Only shared data paths accepted')
        loaded=read_image(path,image['id'],image)
        loaded.update({k:v for k,v in image.items() if k not in ('array','path','shape','transform','raster_metadata')})
        images.append(loaded)
    if len(images)!=2:raise HTTPException(422,'Two images required')
    output=run({**payload['bundle'],'images':images},payload['call'])
    return output
