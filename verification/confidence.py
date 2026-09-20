"""Separate score semantics and evidence-gated decision policy."""
import math


def normalize_score(score, semantics='uncalibrated_model_score'):
    if score is None:return None
    if isinstance(score,bool) or not isinstance(score,(int,float)) or not math.isfinite(score) or not 0<=score<=1:
        raise ValueError('Specialist confidence must be finite and between 0 and 1')
    # Scores already share the [0,1] range. Do not pretend min-max scaling calibrates them.
    return {'value':float(score),'semantics':semantics,'calibrated':False}


def decision(verification, quality, outputs, consensus):
    usable=[o for o in outputs if o.get('status','complete') not in ('failed','unavailable')]
    if quality<.15:
        return {'status':'INSUFFICIENT_EVIDENCE','code':'INSUFFICIENT_EVIDENCE',
                'reason':'Input usability is too low for a reliable semantic conclusion.',
                'needed':'Upload imagery with valid pixels, adequate contrast, and less cloud or nodata.'}
    if not usable:
        return {'status':'MODEL_FAILURE','code':'MODEL_UNAVAILABLE','reason':'No specialist returned usable output.',
                'needed':'Restore a specialist service or load its documented checkpoint.'}
    if verification.get('alignment_quality')=='POOR':
        verification['trust_score']=min(verification['trust_score'], .40)
    if verification.get('alignment_quality')=='WARNING':
        verification['trust_score']=min(verification['trust_score'], .79)
    if consensus=='disagreement':
        verification['trust_score']=min(verification['trust_score'], .60)
    if verification.get('evidence_support', 0) < .50 and verification.get('alignment_quality'):
        verification['trust_score']=min(verification['trust_score'], .65)
    measurements=any(any(m.get('fraction') is not None for m in o.get('measurements',[])) for o in usable)
    if measurements:
        return {'status':'MEASURED_ONLY','code':None,'reason':'Physical proxies were measured; semantic model confidence is unavailable.',
                'needed':'Use independent labels to establish land-cover truth.'}
    if not verification['verification_coverage'] and verification['neural_confidence']<=0:
        return {'status':'INSUFFICIENT_EVIDENCE','code':'INSUFFICIENT_EVIDENCE',
                'reason':'No supported neural answer or independent claim evidence is available.',
                'needed':'Provide the required bands/calibration or a supported model. Available physical measurements remain below.'}
    if verification['trust_score']<.35 or consensus=='disagreement':
        return {'status':'LOW_TRUST','code':'LOW_CONFIDENCE','reason':'Evidence is weak or conflicting; candidate results must not be treated as a definitive answer.',
                'needed':'Check alignment, calibration and input bands; compare with labeled reference data.'}
    return {'status':'ANSWERED','code':None,'reason':'Candidate findings and their independently checkable evidence are available.',
            'needed':None}
