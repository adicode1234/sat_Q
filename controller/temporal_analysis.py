"""Evidence-first orchestration for generic before/after questions."""
import re

import numpy as np

from models.change_mask.model import run as run_change_mask
from models.change_vqa.model import run as run_change_vqa
from models.grounding.model import run as run_grounding
from gateway.spatial import unpack_mask


SUBJECTS = {
    'water': ('water', 'river', 'lake', 'channel'),
    'vegetation': ('vegetation', 'forest', 'tree', 'trees', 'grass'),
    'built_up': ('building', 'buildings', 'built-up', 'built up', 'settlement'),
    'road': ('road', 'roads'),
}


def _subjects(query):
    q = query.lower()
    return [kind for kind, words in SUBJECTS.items() if any(word in q for word in words)]


def _ground(bundle, image, subject):
    single = {**bundle, 'images': [image]}
    return run_grounding(single, {'query': subject.replace('_', ' '), 'params': {'box_threshold': .35, 'text_threshold': .25}})


def _box_mask_area(claims, mask):
    area = 0
    for claim in claims:
        box = claim.get('region')
        if isinstance(box, list) and len(box) == 4:
            x1, y1, x2, y2 = (max(0, int(v)) for v in box)
            area += int(mask[y1:min(y2, mask.shape[0]), x1:min(x2, mask.shape[1])].sum())
    return area


def run(bundle, call):
    before, after = bundle['images']
    mask_output = run_change_mask(bundle, call)
    vqa_output = run_change_vqa(bundle, call)
    mask = unpack_mask(mask_output['raw_mask'])
    valid = np.isfinite(before['array']).all(0) & np.isfinite(after['array']).all(0)
    overlap = float(valid.mean())
    changed_fraction = float(mask.sum() / max(valid.sum(), 1))
    alignment = (bundle.get('validation', {}).get('alignment') or [{}])[0]
    alignment_class = alignment.get('alignment_class', 'WARNING' if before.get('visual_only') else 'GOOD')
    if alignment_class not in ('GOOD', 'WARNING', 'POOR'):
        alignment_class = 'WARNING'
    mask_quality = float(min(1, max(0, .55 + min(changed_fraction, .35)))) if changed_fraction else .2
    evidence = {
        'type': 'pixel_change', 'claim_type': 'visible_change', 'supported': changed_fraction > 0,
        'changed_fraction': changed_fraction, 'valid_overlap_fraction': overlap,
        'alignment_quality': alignment_class, 'alignment': alignment,
        'mask_quality': round(mask_quality, 4),
        'evidence_strength': round(.45 * mask_quality + .3 * overlap + .25 * (1 if alignment_class == 'GOOD' else .55 if alignment_class == 'WARNING' else .1), 4),
        'limitations': ['Appearance change is not semantic proof'],
    }
    grounded = {}
    claims = [{'type': 'visible_change', 'claim_type': 'VISIBLE_CHANGE', 'fraction': changed_fraction,
               'subject': 'appearance', 'image_id': before['id']}]
    for subject in _subjects(call['query']):
        try:
            b = _ground(bundle, before, subject)
            a = _ground(bundle, after, subject)
            b_claims = b.get('claims', []); a_claims = a.get('claims', [])
            b_area = sum(max(0, c['region'][2] - c['region'][0]) * max(0, c['region'][3] - c['region'][1]) for c in b_claims if isinstance(c.get('region'), list))
            a_area = sum(max(0, c['region'][2] - c['region'][0]) * max(0, c['region'][3] - c['region'][1]) for c in a_claims if isinstance(c.get('region'), list))
            changed_in_regions = _box_mask_area(b_claims + a_claims, mask)
            grounded[subject] = {'before': b, 'after': a, 'before_area_pixels': b_area, 'after_area_pixels': a_area,
                                 'region_delta': (a_area - b_area) / max(b_area, 1),
                                 'change_mask_intersection': changed_in_regions,
                                 'spatial_support': bool(b_claims and a_claims and changed_in_regions)}
            claims.append({'type': 'semantic_region_change', 'claim_type': 'SEMANTIC_REGION_CHANGE', 'subject': subject,
                           'direction': 'increase' if a_area > b_area else 'decrease' if a_area < b_area else 'unchanged',
                           'fraction': changed_fraction, 'image_id': before['id'],
                           'grounding_subject': subject})
        except Exception as exc:
            grounded[subject] = {'status': 'GROUNDING_UNAVAILABLE', 'error': type(exc).__name__}
    answer = (f'TEMPORAL CHANGE SUMMARY\n\nVisible appearance change: {"Detected" if changed_fraction else "Not detected"}\n'
              f'Candidate changed pixels: {changed_fraction:.1%}\nAlignment: {alignment_class}\n'
              f'Valid overlap: {overlap:.1%}\n\nSemantic interpretation requires independent before/after localization.')
    return {
        'answer': answer, 'short_answer': answer.split('\n', 1)[0],
        'neural_confidence': vqa_output.get('neural_confidence', 0),
        'raw_neural_confidence': vqa_output.get('raw_neural_confidence'),
        'claims': claims, 'mode': 'temporal_change_analysis', 'overlay': mask_output.get('overlay'),
        'raw_mask': mask_output.get('raw_mask'), 'heatmap': mask_output.get('heatmap'),
        'change_fraction': changed_fraction, 'changed_pixel_count': mask_output.get('changed_pixel_count'),
        'measurements':[{'image_id':before['id'],'measurement':'Appearance-change threshold proxy',
                         'fraction':changed_fraction,'valid_pixels':int(valid.sum())}],
        'comparable_pixel_count': mask_output.get('comparable_pixel_count'),
        'temporal_evidence': evidence, 'grounding_before_after': grounded,
        'change_vqa': {'answer': vqa_output.get('short_answer'), 'confidence': vqa_output.get('neural_confidence', 0),
                       'status': 'auxiliary_unverified'},
        'limitations': ['RGB imagery cannot establish spectral vegetation change without NIR.',
                        'Grounding localizes candidate regions; it is not ground truth.']
    }
