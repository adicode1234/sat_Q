"""Input-aware routing and inference instructions, never query-to-answer templates."""
import re
from gateway.errors import InputError

SPECIALISTS = {'SINGLE': ('VQA', 'GeoChat'), 'BITEMPORAL_PAIR': ('CHANGE_VQA', 'TEOChat'),
               'CROSS_MODAL_PAIR': ('FUSION_ANALYSIS', 'EarthMind')}
COMMON = '''Evaluate the imagery independently of any premise in the question. Preserve uncertainty.
Distinguish observed, inferred, uncertain and unsupported statements. Do not invent counts,
coordinates, boxes, masks, changes or confidence percentages. Report only actual evidence.
Return answer verbatim plus optional observations, evidence and uncertainty in the runtime contract.'''
POLICIES = {
 'GeoChat': 'Analyze the supplied single image. Precise counts require distinguishable objects. Grounding requires actual tool output. Water alone does not establish flooding.',
 'TEOChat': 'Compare corresponding before and after regions. Where supported distinguish before, after, added, removed, reduced, expanded and unchanged. Appearance or seasonal differences do not alone establish physical land-cover change.',
 'EarthMind': 'Use BOTH optical and SAR inputs. Separate optical evidence, SAR evidence, agreement, disagreement and fused interpretation. Missing SAR semantic evidence must remain unavailable. Do not assume SAR detects hidden objects. Retain conflicts and cloud limitations.'}


def route(bundle, query):
    scenario = bundle['scenario']
    images = bundle['images']
    q = query.lower()
    fusion = bool(re.search(r'\b(cross[ -]?modal|fusion|fuse|both sensors|sensors (?:agree|disagree)|modalities)\b', q)
                  or ('optical' in q and 'sar' in q))
    temporal = bool(re.search(r'\b(chang(?:e|ed|es)|before|after|earlier|previous|increas\w*|decreas\w*|expand\w*|demolish\w*|newly|disappear\w*|added|removed|constructed|appeared|grown|growth|different now|second image)\b', q))
    if fusion and {i['modality'] for i in images} != {'optical', 'SAR'}:
        missing = 'SAR' if any(i['modality'] == 'optical' for i in images) else 'optical'
        raise InputError(f'Optical/SAR comparison requires a corresponding {missing} image.', 'MISSING_MODALITY',
                         'Supply a co-registered optical + SAR pair and select Optical + SAR.')
    if temporal and scenario == 'SINGLE':
        raise InputError('Temporal change cannot be established from one image.', 'SECOND_IMAGE_REQUIRED',
                         'Supply an earlier and later image of the same area in Before / after mode.')
    if temporal and scenario == 'CROSS_MODAL_PAIR':
        raise InputError('A cross-sensor pair alone does not establish temporal change.', 'TEMPORAL_REFERENCE_REQUIRED',
                         'Supply corresponding before/after observations for temporal analysis.')
    if scenario not in SPECIALISTS:
        raise InputError('Named specialists support one image or one corresponding pair.', 'UNSUPPORTED_TASK',
                         'Select a single image or before/after pair; legacy multi-date measurements require explicit legacy mode.')
    expected = 1 if scenario == 'SINGLE' else 2
    if len(images) != expected:
        raise InputError(f'{scenario} requires {expected} image(s).')
    task, specialist = SPECIALISTS[scenario]
    if scenario == 'SINGLE' and re.search(r'\b(where|locate|highlight|ground|outline|find|mark)\b', q):
        task = 'GROUNDING'
    return task, specialist
