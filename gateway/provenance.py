"""Content-addressed processing/model provenance, without local filesystem leaks."""
from functools import lru_cache
from pathlib import Path
import hashlib
import importlib.metadata

ROOT=Path(__file__).resolve().parents[1]


@lru_cache(maxsize=64)
def _digest(path,size,mtime):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def file_digest(path):
    path=Path(path);stat=path.stat()
    return _digest(str(path),stat.st_size,stat.st_mtime_ns)


def processing_provenance(bundle,outputs):
    artifacts={}
    for relative in ['rgb_adapter.npz','rgb_water_real.npz','rgb_water_segformer/model.safetensors','water_real/optical.npz','water_real/sar.npz','water_real/joint.npz','vilt_lora/adapter_model.safetensors','change_siamese/weights.pt','fusion_cross_attention/weights.pt']:
        path=ROOT/'models/checkpoints'/relative
        if path.exists():artifacts[relative]=file_digest(path)
    code=hashlib.sha256()
    for folder in ('gateway','controller','verification','fusion_engine','models'):
        for path in sorted((ROOT/folder).rglob('*.py')):code.update(path.read_bytes())
    return {'processing_version':'2.0','processing_sha256':code.hexdigest(),'checkpoint_artifacts':artifacts,
            'inputs':[{'id':i['id'],'sha256':i['sha256'],'source_type':i['source_type']} for i in bundle['images']],
            'executed_models':[{'model':o['model'],'mode':o['mode'],'status':o['status']} for o in outputs],
            'seed':None,'seed_note':'Inference uses eval mode; no randomized inference seed is set.',
            'validation':bundle['validation'],'rasterio_version':importlib.metadata.version('rasterio')}
