"""Text-guided neural grounding and labelled-data water segmentation."""
import os,re
import numpy as np

def extract_water_boxes(image,query=None):
    from controller.scene_analyzer import analyze_water_morphology
    from models.rgb_water import predict_segmentation
    mapped,p,stats,valid=predict_segmentation(image)
    result=analyze_water_morphology((mapped==2)&valid)
    boxes=[]
    for component in result['components']:
        x1,y1,x2,y2=component['box'];selected=(mapped[y1:y2,x1:x2]==2)&valid[y1:y2,x1:x2]
        score=float(np.nanmean(p[y1:y2,x1:x2][selected]))
        boxes.append({**component,'score':score})
    return sorted(boxes,key=lambda b:b['area'],reverse=True)[:20]

def coarse_run(bundle,call):
    return {'status':'unavailable','answer':'No suitable learned grounding result is available for this input.','neural_confidence':0,'claims':[],'mode':'grounding_unavailable','overlay':None}

def run(bundle,call):
    image=bundle['images'][0]
    if image.get('modality')!='optical':return coarse_run(bundle,call)
    query=call['query'];water=bool(re.search(r'\b(water|river|lake|stream|reservoir|flood|channel|pond|waterbody)\b',query.lower()))
    if water:
        try:
            from models.rgb_water import predict_segmentation
            mapped,prob,stats,valid=predict_segmentation(image)
            from models.change_mask.model import encode
            from gateway.spatial import pack_mask
            mask=(mapped==2)&valid;fraction=float(mask.sum()/valid.sum())
            if fraction<0.005:
                return {'status':'complete','answer':'No significant surface water detected in this scene (<0.5%).',
                        'neural_confidence':0.35,'claims':[{'type':'water','region':'whole_image','fraction':fraction,'image_id':image['id'],'sampling_basis':'valid_rgb'}],
                        'fractions':{'water':fraction},'mode':'learned_rgb_water_grounding','overlay':None,'raw_mask':pack_mask(mask)}
            return {'status':'complete','answer':f'Learned RGB model estimates {fraction:.1%} water candidate coverage. Sensor transfer is uncalibrated; shape alone cannot prove flowing water.',
                    'neural_confidence':min(float(np.maximum(prob[valid],1-prob[valid]).mean()),.4096),'claims':[{'type':'water','region':'whole_image','fraction':fraction,'image_id':image['id'],'sampling_basis':'valid_rgb'}],
                    'fractions':{'water':fraction},'mode':'learned_rgb_water_grounding','overlay':encode(mask,image['id']),'raw_mask':pack_mask(mask)}
        except (ImportError,OSError,RuntimeError,ValueError):pass
    if os.environ.get('SATQUERY_USE_DINO','1')!='1':return coarse_run(bundle,call)
    try:
        from models.grounding.dino import detect
        params=call.get('params',{});boxes=detect(image,query,params.get('box_threshold',.35),params.get('text_threshold',.25))
    except (ImportError,OSError,RuntimeError,ValueError):return coarse_run(bundle,call)
    if not boxes:return {'status':'complete','answer':'No regions exceeded the detector threshold. This does not establish absence.','neural_confidence':0,'claims':[],'mode':'pretrained_grounding_dino_no_detection','overlay':None}
    claims=[]
    for b in boxes:
        label=b['label'].lower()
        kind=next((k for k,words in {'water':['water','river','lake','pond'],'vegetation':['tree','forest','vegetation'],'built_up':['building','house'],'road':['road','bridge','highway']}.items() if any(w in label for w in words)),'grounded_object')
        claims.append({'type':kind,'region':b['box'],'value':b['label'],'image_id':image['id']})
    return {'status':'complete','answer':f'Pretrained detector returned {len(boxes)} candidate regions. Scores are uncalibrated; overlapping boxes are not a verified object count.',
            'neural_confidence':float(np.mean([b['score'] for b in boxes])),'claims':claims,'mode':'pretrained_grounding_dino','overlay':{'type':'bbox','data':boxes,'width':image['shape'][1],'height':image['shape'][0],'image_id':image['id']}}
