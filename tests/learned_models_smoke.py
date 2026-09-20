"""Explicit checkpoint acceptance, separate from lightweight unit tests."""
import json,os
from pathlib import Path
import numpy as np
from gateway.validation import validate
from controller.pipeline import run_pipeline
from models.grounding.dino import detect
from models.fusion_optical_sar.model import learned_fusion
ROOT=Path(__file__).resolve().parents[1]

def main():
    os.environ['SATQUERY_USE_DINO']='1'
    image=validate([ROOT/'data/vrsbench/P0003_0002.png'],[{'benchmark_source':'https://huggingface.co/datasets/xiang709/VRSBench'}],'SINGLE')['images'][0]
    boxes=detect(image,'vehicle',.25,.2)
    assert boxes,'Expected local pretrained DINO inference to yield candidates on the acceptance fixture'
    demo=json.loads((ROOT/'data/demo/manifest.json').read_text())[3]
    bundle=validate([ROOT/p for p in demo['paths']],demo['options'],demo['scenario'])
    optical,sar=bundle['images'];first,_,valid=learned_fusion(optical,sar)
    changed={**sar,'array':np.full_like(sar['array'],-25)}
    second,_,_=learned_fusion(optical,changed)
    assert (first[valid]!=second[valid]).any(),'Learned joint predictions must respond to SAR changes'
    out=run_pipeline([ROOT/p for p in demo['paths']],demo['options'],demo['scenario'],demo['query'])
    assert 'synthetic_trained_cross_attention' in out['specialists'][0]['mode']
    assert any(c['claim']['value']=='cross-attention fused fraction' for c in out['verification']['checks'])
    result={'grounding_dino':{'status':'passed','boxes':boxes,'quality_validated':False},
            'fusion':{'status':'passed','sar_perturbation_changed_fraction':float((first[valid]!=second[valid]).mean()),'mode':out['specialists'][0]['mode'],'training_scope':'synthetic only'}}
    (ROOT/'tests/learned_models_results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
