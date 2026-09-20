"""Task-specific metrics; only compute against supplied labels."""
import numpy as np


def mask_metrics(prediction,reference):
    pred=np.asarray(prediction,dtype=bool);ref=np.asarray(reference,dtype=bool)
    if pred.shape!=ref.shape:raise ValueError('Mask dimensions must match')
    tp=int((pred&ref).sum());fp=int((pred&~ref).sum());fn=int((~pred&ref).sum())
    return {'iou':tp/(tp+fp+fn) if tp+fp+fn else 1.,
            'dice':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 1.,
            'precision':tp/(tp+fp) if tp+fp else None,'recall':tp/(tp+fn) if tp+fn else None}


def box_iou(a,b):
    intersection=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
    union=max(0,a[2]-a[0])*max(0,a[3]-a[1])+max(0,b[2]-b[0])*max(0,b[3]-b[1])-intersection
    return intersection/union if union else 0.
