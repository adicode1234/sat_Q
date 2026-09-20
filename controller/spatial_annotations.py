"""Validate visual model locations without synthesizing missing geometry."""
import math


def visual_overlays(detections, images):
    if not isinstance(detections, list):
        return []
    grouped = {image['id']: [] for image in images}
    for item in detections[:200]:
        if not isinstance(item, dict):
            continue
        image_id, label, box = item.get('image_id'), item.get('label'), item.get('box')
        if not isinstance(image_id, str) or image_id not in grouped:
            continue
        if not isinstance(label, str) or not label.strip() or not isinstance(box, list) or len(box) != 4:
            continue
        if not all(type(v) in (int, float) and math.isfinite(v) and 0 <= v <= 1 for v in box):
            continue
        if box[2] <= box[0] or box[3] <= box[1]:
            continue
        entry = {'box': box, 'label': label.strip()[:80]}
        if entry not in grouped[image_id]:
            grouped[image_id].append(entry)
    return [
        {'type': 'bbox', 'width': 1, 'height': 1, 'image_id': image_id,
         'label': 'Approximate AI object locations', 'data': boxes}
        for image_id, boxes in grouped.items() if boxes
    ]
