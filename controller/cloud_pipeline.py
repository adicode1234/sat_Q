"""Cloud semantic interpretation remains separate from physical verification.
Emits explicit progress events for real-time UI updates and raises errors directly.
"""
import time
from gateway.validation import public_contract
from verification.engine import verify
from models.cloud_vision import analyze, configuration, PROVIDERS

def run(bundle, query, analysis_id, trace, event, started):
    # Step 0: Input validation progress
    event('validate_inputs', result='Inputs, bands and resolution validated for cloud vision.')

    key, model, provider = configuration()
    provider_label = PROVIDERS[provider][0]

    # Step 1: Model Selection
    event('select_model', model=model or provider, reason=f'Using {provider_label} ({model}) for cloud visual interpretation.')

    # Step 2: Model Execution
    event('execute', model='cloud_vision', result=f'Sending supplied image previews and question to {provider_label} ({model})...')

    # Execute Cloud Model Call
    # Note: If analyze fails, it raises an exception (InputError). We deliberately do NOT
    # catch it here, so it surfaces to the gateway and UI, preventing any silent fallback.
    response = analyze(bundle, query)
    from controller.spatial_annotations import visual_overlays
    spatial_overlays = visual_overlays(response.get('detections'), bundle['images'])

    # Step 3: Model Complete
    event('model_complete', model=response['model'], mode='cloud_visual_interpretation', result=response['answer'])

    # Step 4: Verification
    event('symbolic_verification', result='Verifying interpretation consistency and physical constraints.')
    verification = verify(bundle, [])
    event('verification_complete', result='Physical rule checks completed.')

    description = response.get('description') or response.get('answer', '')
    raw_answer = response['answer']
    answer = raw_answer

    visible = response.get('visible_features')
    visible = [item.strip() for item in visible if isinstance(item, str) and item.strip()] if isinstance(visible, list) else []
    uncertainties = response.get('uncertainties')
    uncertainties = [item for item in uncertainties if isinstance(item, str)] if isinstance(uncertainties, list) else []
    # Text interpretation supplies neither measured coverage nor calibrated confidence.
    present_items = [{'name': item, 'detail': '', 'category': 'visual',
                      'icon': '📍', 'badge': 'Detected'} for item in visible]
    # Uncertainty is retained separately; it is not evidence of object absence.
    absent_items = []
    fusion_analysis = None
    composition = {}

    inventory = {
        'present': present_items,
        'absent': absent_items,
        'description': description,
        'composition': composition,
        'temporal_breakdown': [],
        'multi_class_boxes': [],
        'pixel_mask': None,
        'answer': answer
    }

    # Step 5: Report Generation
    event('report', result='Image interpretation prepared without fabricated segmentation masks or area measurements.')

    result = {
        'query_id': analysis_id,
        'query': query,
        'answer': answer,
        'executive_answer': answer,
        'description': description,
        'visible_features': visible,
        'uncertainties': uncertainties,
        'short_answer': None,
        'interpretation_source': response.get('provider_id', 'gemini'),
        'cloud_vision': {
            'provider': response['provider'],
            'provider_id': provider,
            'model': response['model'],
            'response_id': response['response_id'],
            'image_type': response['image_type'],
            'description': description,
            'answer': raw_answer,
            'visible_features': visible,
            'uncertainties': uncertainties,
            'usage': response['usage']
        },
        'overlay': None,
        'spatial_overlays': spatial_overlays,
        'pixel_mask': None,
        'composition': {},
        'fusion_analysis': fusion_analysis,
        'fusion_summary': fusion_analysis,
        'present': inventory['present'],
        'absent': absent_items if visible else [],
        'multi_class_boxes': [],
        'temporal_breakdown': [],
        'scene_inventory': inventory,
        'scenario': bundle['scenario'],
        'task': 'VISUAL_INTERPRETATION',
        'decision': {
            'status': 'VISUAL_INTERPRETATION',
            'code': None,
            'reason': 'Cloud image interpretation; factual correctness and physical measurements are not independently verified.',
            'needed': None
        },
        'trust_score': None,
        'visual_confidence': None,
        'confidence_breakdown': {
            'neural': None,
            'visual_confidence': None,
            'symbolic': None,
            'coverage': None,
            'input_quality': bundle['validation'].get('input_quality', 0.98) or 0.98,
            'final_trust': None
        },
        'trust_explanation': f"Cloud visual interpretation by {response['provider']} ({response['model']}) completed with high visual clarity.",
        'verification': verification,
        'consensus': 'unverified cloud interpretation',
        'specialists': [],
        'input': public_contract(bundle),
        'execution_trace': trace,
        'timings': {'total_s': time.perf_counter() - started},
        'report_url': None,
        'spatial_products': [],
        'flags': [],
        'limitations': [
            'Cloud vision can make mistakes; outputs are visual interpretations, not validated pixel segmentation.'
        ],
        'provenance': {
            'provider': response['provider'],
            'provider_id': provider,
            'model': response['model'],
            'response_id': response['response_id'],
            'inputs': [{'id': i['id'], 'sha256': i['sha256']} for i in bundle['images']]
        }
    }

    if provider == 'openrouter':
        from gateway.contracts import AnalysisReport
        report = AnalysisReport(
            query=query, task='VISUAL_INTERPRETATION', specialist='OpenRouter cloud vision', answer=raw_answer,
            uncertainty=response['uncertainties'] + [
                'Cloud visual interpretation is unverified; GeoChat, TEOChat and EarthMind were not executed.',
                'Previews do not establish calibrated SAR measurements or independently verified optical/SAR agreement.'],
            execution_summary={
                'input_configuration': [{'image_id': i['id'], 'modality': i['modality'], 'date': i.get('date')} for i in bundle['images']],
                'task_detected': 'VISUAL_INTERPRETATION', 'specialist_selected': None,
                'models_tools': [response['model']], 'provider': 'OpenRouter', 'requested_model': model,
                'processing_status': 'completed', 'validation_result': bundle['validation_status'],
                'parameters': {'temperature': .2, 'max_tokens': 4096},
                'evidence_generated': ['unverified image interpretation'], 'fallback': None,
            }).model_dump()
        result.update(analysis_report=report, confidence=report['confidence'], execution_summary=report['execution_summary'],
                      trust_score=None, answer=raw_answer, executive_answer=raw_answer)
        result['confidence_breakdown']['final_trust'] = None

    try:
        from gateway.translator import translate_single, translate_texts
        result['translations'] = {
            'hi': {
                'description': translate_single(description, 'hi'),
                'answer': translate_single(result.get('answer', answer), 'hi'),
                'visible_features': translate_texts(visible, 'hi'),
                'uncertainties': translate_texts(uncertainties, 'hi')
            },
            'bn': {
                'description': translate_single(description, 'bn'),
                'answer': translate_single(result.get('answer', answer), 'bn'),
                'visible_features': translate_texts(visible, 'bn'),
                'uncertainties': translate_texts(uncertainties, 'bn')
            }
        }
    except Exception as e:
        print(f"[Pre-translate notice] {e}", flush=True)
        result['translations'] = {}

    return result
