"""Agreement checks are abstention rules, not calibrated accuracy estimates."""
import numpy as np

def water_agreement(first,second,valid):
    a=np.asarray(first,bool)&valid;b=np.asarray(second,bool)&valid
    union=int((a|b).sum());intersection=int((a&b).sum())
    iou=intersection/union if union else None
    first_frac=float(a.sum()/max(valid.sum(),1))
    second_frac=float(b.sum()/max(valid.sum(),1))
    both_minimal=(first_frac<0.02 and second_frac<0.02)
    reliable=bool(both_minimal or (union and iou and iou>=.35))
    reason=('Both models indicate minimal or absent surface water in the scene.' if both_minimal
            else 'Two local water models agree on candidate extent.' if reliable
            else 'The local water models show variance on water boundaries in standard RGB imagery; water extent is estimated/approximate.')
    return {'mask_iou':iou,'first_fraction':first_frac,
            'second_fraction':second_frac,
            'reliable':reliable,
            'reason':reason,
            'semantics':'Conservative model-agreement gate, not independent validation or probability of correctness.'}

def apply_answer_gate(fused,gate):
    """A rejected or low-trust answer cannot survive as a direct finding."""
    if gate['status'] in ('LOW_TRUST','INSUFFICIENT_EVIDENCE','MODEL_FAILURE'):
        if fused.get('short_answer'):fused['candidate_short_answer']=fused['short_answer']
        fused['short_answer']=None
