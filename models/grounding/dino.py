"""Local pretrained Grounding DINO with bounded, text-guided detections."""
import re
import threading
from pathlib import Path
import numpy as np
from gateway.validation import rgb
_loaded=None
_lock=threading.Lock()

def clean_grounding_prompt(query: str) -> str:
    q = query.lower().strip().rstrip('?.!,')
    
    # Check for multi-class detection first
    if any(w in q for w in ('all', 'everything', 'sabko', 'sare', 'identify all', 'detect all', 'overview', 'features')):
        return 'river . road . bridge . buildings . trees .'

    # Check for direct key domains
    if any(w in q for w in ('river', 'water', 'lake', 'stream', 'reservoir', 'waterway', 'canal', 'flood', 'pond')):
        return 'river . lake . pond . water body .'
    if any(w in q for w in ('forest', 'vegetation', 'trees', 'tree', 'plants', 'crop', 'field', 'greenery')):
        return 'forest . vegetation . trees .'
    if any(w in q for w in ('building', 'buildings', 'house', 'houses', 'settlement', 'urban', 'structure', 'infrastructure')):
        return 'buildings . houses . urban structure .'
    if any(w in q for w in ('road', 'roads', 'highway', 'transport', 'bridge', 'street', 'corridor')):
        return 'road . highway . bridge .'

    patterns = [
        r'^(?:can you|could you|please)?\s*(?:show|detect|find|see|locate|highlight|identify|point out)\s+(?:me\s+)?(?:the\s+|all\s+|any\s+)?',
        r'^(?:i\s+(?:want|would like)\s+to\s+(?:see|find|detect|locate|view))\s+(?:the\s+|all\s+|any\s+)?',
        r'^(?:is\s+there\s+(?:any\s+|a\s+)?|are\s+there\s+(?:any\s+)?|is\s+that\s+(?:any\s+|a\s+)?)',
        r'^(?:where\s+is\s+(?:the\s+)?|where\s+are\s+(?:the\s+)?)',
        r'^(?:what\s+is\s+(?:the\s+)?|what\s+are\s+(?:the\s+)?)',
    ]
    cleaned = q
    for pat in patterns:
        cleaned = re.sub(pat, '', cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r'\s*(?:in\s+this\s+(?:image|scene|satellite\s+image|observation|photo)|in\s+the\s+(?:image|scene|photo)|here|on\s+the\s+map)\s*$', '', cleaned, flags=re.IGNORECASE).strip()
    
    terms = ['river', 'water body', 'lake', 'stream', 'ocean', 'sea', 'water',
             'vegetation', 'forest', 'trees', 'tree', 'grass', 'crop',
             'building', 'buildings', 'house', 'road', 'bridge', 'urban']
    matched_terms = [t for t in terms if t in q]
    
    parts = []
    if cleaned and len(cleaned) > 1:
        parts.append(cleaned)
    for t in matched_terms:
        if t not in parts:
            parts.append(t)
            
    if not parts:
        parts = [q]
    return ' . '.join(parts) + ' .'

def detect(image,query,threshold=.35,text_threshold=.25):
    global _loaded
    import torch
    from PIL import Image
    from transformers import AutoProcessor,AutoModelForZeroShotObjectDetection
    path=Path(__file__).resolve().parents[1]/'checkpoints/grounding_dino'
    with _lock:
        if _loaded is None:
            torch.set_num_threads(4)
            processor=AutoProcessor.from_pretrained(path,local_files_only=True)
            model=AutoModelForZeroShotObjectDetection.from_pretrained(path,local_files_only=True).eval()
            _loaded=processor,model
    processor,model=_loaded
    prompt=clean_grounding_prompt(query)
    picture=Image.fromarray(rgb(image))
    inputs=processor(images=picture,text=prompt,return_tensors='pt')
    with torch.inference_mode():output=model(**inputs)
    results=processor.post_process_grounded_object_detection(output,inputs.input_ids,threshold=threshold,text_threshold=text_threshold,target_sizes=[(picture.height,picture.width)])[0]
    boxes=[]
    for box,score,label in zip(results['boxes'],results['scores'],results.get('text_labels',results.get('labels',[]))):
        x1,y1,x2,y2=box.tolist();coords=[max(0,int(x1)),max(0,int(y1)),min(picture.width,int(np.ceil(x2))),min(picture.height,int(np.ceil(y2)))]
        if coords[2]>coords[0] and coords[3]>coords[1]:boxes.append({'box':coords,'label':str(label),'score':float(score)})
    return sorted(boxes,key=lambda b:b['score'],reverse=True)[:20]

