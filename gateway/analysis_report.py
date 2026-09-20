"""Lossless specialist report normalization; no scientific findings are synthesized."""
from gateway.contracts import AnalysisReport, RuntimeResponse, TaskEvidence
from gateway.validation import public_contract


def normalize(raw, bundle, query, task, specialist, trace, error=None):
    evidence = TaskEvidence()
    observations = []
    warnings = list(bundle['validation'].get('warnings', []))
    answer = f'{specialist} unavailable; no specialist findings were generated.'
    model = None
    if raw is not None:
        response = RuntimeResponse.model_validate(raw)
        if response.specialist != specialist or not response.answer.strip() or not response.model.strip():
            raise ValueError('Malformed specialist answer or provenance')
        evidence = response.evidence
        ids = {i['id'] for i in bundle['images']}
        modalities = {i['id']: i['modality'] for i in bundle['images']}
        for category, items in evidence:
            for item in items:
                if not set(item.image_ids) <= ids:
                    raise ValueError('Evidence references an image that was not supplied')
                if category in ('optical', 'sar'):
                    expected = 'SAR' if category == 'sar' else 'optical'
                    if any(modalities[i] != expected for i in item.image_ids):
                        raise ValueError('Evidence modality does not match its source image')
                if category in ('added', 'removed', 'reduced', 'expanded', 'unchanged') and bundle['scenario'] != 'BITEMPORAL_PAIR':
                    raise ValueError('Change evidence requires a temporal pair')
                if category in ('before', 'after'):
                    if bundle['scenario'] != 'BITEMPORAL_PAIR' or set(item.image_ids) != {bundle['images'][category == 'after']['id']}:
                        raise ValueError('Temporal evidence must reference the corresponding date')
                if category in ('agreement', 'disagreement') and (bundle['scenario'] != 'CROSS_MODAL_PAIR' or set(item.image_ids) != ids):
                    raise ValueError('Cross-modal relations must reference both sensors')
        for item in response.observations:
            if not set(item.image_ids) <= ids:
                raise ValueError('Observation references an image that was not supplied')
        answer, observations, model = response.answer, response.observations, response.model
        warnings.extend(response.uncertainty)
    if specialist == 'EarthMind':
        if not evidence.optical or not evidence.sar:
            warnings.append('Modality-specific evidence is incomplete: optical/SAR fusion is not independently established.')
        if not evidence.sar:
            warnings.append('SAR-specific semantic evidence is unavailable; mentioning SAR does not establish sensor contribution.')
    if specialist == 'TEOChat':
        if not evidence.before or not evidence.after:
            warnings.append('Separate before/after evidence is unavailable or incomplete.')
        warnings.append('Seasonal, illumination and registration differences may resemble physical change.')
    if task == 'GROUNDING':
        warnings.append('This runtime contract supplies text only; no verified grounding overlay was generated.')
    warnings.append('Specialist text is unverified model output. No calibrated confidence mechanism is available.')
    if error:
        warnings.append(error)
    summary = {
        'input_configuration': [{'image_id': i['id'], 'modality': i['modality'], 'date': i.get('date')} for i in bundle['images']],
        'task_detected': task, 'specialist_selected': specialist,
        'models_tools': [model] if model else [], 'parameters': {},
        'processing_status': 'failed' if error else 'completed',
        'validation_result': bundle['validation_status'],
        'pairing': {'alignment_diagnostics': bundle['validation'].get('alignment', []),
                    'limitation': 'Grid/overlap checks and declared ordering do not independently certify sensor co-registration or acquisition dates.'},
        'evidence_generated': [key for key, value in evidence if value],
        'warnings': list(dict.fromkeys(warnings)),
        'cloud_role': 'disabled for specialist reports', 'fallback': None,
    }
    report = AnalysisReport(query=query, task=task, specialist=specialist, answer=answer,
                            observations=observations, evidence=evidence, uncertainty=list(dict.fromkeys(warnings)),
                            execution_summary=summary).model_dump()
    return report


def envelope(report, bundle, analysis_id, trace, elapsed, raw=None):
    failed = report['execution_summary']['processing_status'] == 'failed'
    return {
        **report, 'analysis_report': report, 'query_id': analysis_id,
        'scenario': bundle['scenario'], 'executive_answer': report['answer'], 'short_answer': None,
        'decision': {'status': 'MODEL_FAILURE' if failed else 'UNVERIFIED_MODEL_OUTPUT',
                     'code': 'MODEL_UNAVAILABLE' if failed else None, 'reason': report['confidence']['reason']},
        'overlay': None, 'pixel_mask': None, 'composition': {}, 'multi_class_boxes': [],
        'present': [], 'absent': [], 'spatial_products': [],
        'trust_score': None, 'visual_confidence': None,
        'confidence_breakdown': {'neural': None, 'symbolic': None, 'coverage': None,
                                 'input_quality': bundle['validation']['input_quality'], 'final_trust': None},
        'verification': {'checks': [], 'physical_statistics': {}, 'trust_score': None},
        'specialists': [] if raw is None else [{'model': raw['model'], 'specialist': raw['specialist'],
                       'status': 'complete', 'mode': 'specialist_runtime', 'raw_output': raw}],
        'input': public_contract(bundle), 'execution_trace': trace, 'report_url': None,
        'timings': {'total_s': elapsed}, 'limitations': report['uncertainty'],
        'flags': [], 'provenance': {'specialist': report['specialist'],
             'models': report['execution_summary']['models_tools'],
             'inputs': [{'id': i['id'], 'sha256': i['sha256']} for i in bundle['images']]},
    }
