"""Deterministic verification; unknown evidence never becomes agreement."""
import numpy as np

INDEX_BANDS={'NDVI':('nir','red'),'NDWI':('green','nir'),'NDBI':('swir','nir')}
CLAIM_INDEX={'water':('NDWI',.15),'vegetation':('NDVI',.3),'built_up':('NDBI',.1)}

def normalized_difference(a,b):
    den=a+b
    return np.divide(a-b,den,out=np.full_like(a,np.nan,dtype=float),where=np.isfinite(a)&np.isfinite(b)&(np.abs(den)>1e-8))

def summaries(bundle):
    result={}; maps={}
    for image in bundle['images']:
        bands={b:image['array'][n] for n,b in enumerate(image['bands'])}
        item={}; imaps={}
        for name,(a,b) in INDEX_BANDS.items():
            if a in bands and b in bands:
                v=normalized_difference(bands[a],bands[b]); valid=v[np.isfinite(v)]
                item[name]={'mean':float(valid.mean()) if valid.size else None,'valid_fraction':float(np.isfinite(v).mean())}
                imaps[name]=v
        if image['modality']=='SAR':
            if image['sar_units'] in ('db','linear'):
                reference=next((b for b in ('vv','hh') if b in image['bands']),image['bands'][0])
                v=bands[reference].astype(float)
                if image['sar_units']=='linear':
                    v=10*np.log10(np.where(v>0,v,np.nan))
                finite=v[np.isfinite(v)]
                item['SAR']={'mean_db':float(finite.mean()) if finite.size else None,
                             'std_db':float(finite.std()) if finite.size else None,
                             'dark_fraction':float(np.mean(finite < -17)) if finite.size else None,
                             'band':reference,'interpretation':'Low backscatter supports smooth surfaces; not unique to water'}
                imaps['SAR']=v
            else: item['SAR']={'unavailable':'Specify calibrated SAR units: db or linear'}
        item['coherence']={'unavailable':'Requires complex SLC pair; intensity alone cannot provide interferometric coherence'}
        result[image['id']]=item;maps[image['id']]=imaps
    return result,maps

def verify(bundle, outputs):
    stats,maps=summaries(bundle); checks=[];flags=[]; total=0
    images={i['id']:i for i in bundle['images']}
    for output in outputs:
        temporal_evidence=output.get('temporal_evidence', {})
        temporal_grounding=output.get('grounding_before_after', {})
        for claim in output.get('claims',[]):
            total+=1; kind=claim['type']; imid=claim.get('image_id','img1'); m=maps.get(imid,{})
            result={'claim':claim,'status':'unverified','agreement':None}
            if claim.get('sampling_basis')=='model_valid' and not output.get('valid_mask'):
                result['reason']='Model valid domain differs from full image; aggregate physical fraction cannot verify it'
                checks.append(result);flags.append(f'{kind}: incomplete model coverage; spatially matched verification required');continue
            region=claim.get('region','whole_image')
            def select(a):
                if isinstance(region,list) and len(region)==4:
                    x1,y1,x2,y2=region;return a[y1:y2,x1:x2]
                return a
            v=None; threshold=None
            if region!='whole_image' and not (isinstance(region,list) and len(region)==4 and all(isinstance(x,int) for x in region)):
                result['reason']='Unsupported claim region';checks.append(result);flags.append(f'{kind}: unsupported claim region; unverified');continue
            if kind in CLAIM_INDEX:
                idx,threshold=CLAIM_INDEX[kind]
                if idx in m:
                    v=select(m[idx]);result['evidence']=idx
                elif kind=='water' and 'SAR' in m:
                    v=-select(m['SAR']);threshold=17;result['evidence']='SAR dark-return proxy (ambiguous)'
            elif kind in ('change','visible_change') and len(bundle['images'])==2:
                a,b=bundle['images']; shared=set(maps[a['id']])&set(maps[b['id']])
                shared.discard('SAR')
                if shared:
                    stack=np.stack([np.abs(maps[b['id']][k]-maps[a['id']][k]) for k in sorted(shared)])
                    v=select(np.max(stack,axis=0));threshold=.2;result['evidence']='Maximum spectral-index difference > 0.2'
                elif 'SAR' in maps[a['id']] and 'SAR' in maps[b['id']]:
                    v=select(np.abs(maps[b['id']]['SAR']-maps[a['id']]['SAR']));threshold=3;result['evidence']='SAR intensity difference > 3 dB (not coherence)'
            elif kind=='visible_change' and temporal_evidence:
                result.update(evidence='deterministic change mask', evidence_strength=temporal_evidence.get('evidence_strength', 0),
                              measured_fraction=temporal_evidence.get('changed_fraction', 0),
                              alignment_quality=temporal_evidence.get('alignment_quality', 'WARNING'))
                result['reason']='A mask cannot independently verify its own derived claim'
            elif kind=='semantic_region_change' and temporal_grounding:
                subject=claim.get('grounding_subject')
                evidence=temporal_grounding.get(subject, {})
                if evidence.get('spatial_support') and evidence.get('change_mask_intersection', 0)>0:
                    before_area=float(evidence.get('before_area_pixels', 0));after_area=float(evidence.get('after_area_pixels', 0))
                    direction=claim.get('direction')
                    direction_agreement=(direction=='increase' and after_area>before_area) or (direction=='decrease' and after_area<before_area) or (direction=='unchanged' and after_area==before_area)
                    agreement=.75 if direction_agreement else .25
                    result.update(evidence='before/after grounding intersected with change mask', spatial_support=True,
                                  region_delta=evidence.get('region_delta'), auxiliary_direction_consistency=direction_agreement,
                                  reason='The same grounding boxes generated this claim; independent semantic verification is unavailable')
                else:
                    result['reason']='Before/after semantic localization unavailable; claim remains unverified'
            if v is not None:
                if claim.get('sampling_basis')=='model_valid':
                    from gateway.spatial import unpack_mask
                    domain=select(unpack_mask(output['valid_mask']))
                    if domain.shape!=v.shape:raise ValueError('Claim validity mask and physical evidence grids differ')
                    v=np.where(domain,v,np.nan)
                    result['evidence_pixel_coverage']=float(np.isfinite(v).sum()/max(domain.sum(),1))
                    if result['evidence_pixel_coverage']<.8:
                        result['reason']='Physical evidence covers less than 80% of the model valid domain';v=None
            if v is not None:
                if claim.get('sampling_basis')=='valid_rgb':
                    image=images[imid];valid_rgb=np.isfinite(image['array'][[image['bands'].index(b) for b in ('red','green','blue')]]).all(0)
                    valid_rgb=select(valid_rgb);v=np.where(valid_rgb,v,np.nan)
                    spatial_coverage=float(np.isfinite(v).sum()/max(valid_rgb.sum(),1))
                    result['evidence_pixel_coverage']=spatial_coverage
                    if spatial_coverage<.8:
                        result['reason']='Physical evidence covers less than 80% of the claimed RGB domain';v=None
            if v is not None:
                finite=v[np.isfinite(v)]
                if finite.size:
                    measured=float(np.mean(finite>threshold)); predicted=claim.get('fraction')
                    if claim.get('predicate')=='presence':
                        predicted=1.0;agreement=float(measured>.01)
                    elif isinstance(predicted,(float,int)) and np.isfinite(predicted) and 0<=predicted<=1:
                        agreement=max(0,1-abs(measured-predicted)/max(measured,predicted,.05))
                    else:
                        result['reason']='Claim has no valid fraction or presence predicate';checks.append(result);flags.append(f'{kind}: malformed claim; unverified');continue
                    result.update(measured_fraction=measured,agreement=agreement,status='supported' if agreement>=.75 else 'disagrees')
                    if claim.get('predicate')=='presence':result['status']='supported' if agreement else 'disagrees'
                    if result['status']=='disagrees':flags.append(f"{kind} claim disagrees with {result['evidence']}: specialist {predicted:.0%}, physical proxy {measured:.0%}")
            if result['status']=='unverified':
                result.setdefault('reason','Required independent physical evidence unavailable')
                result['evidence_state']='missing'
                flags.append(f'{kind}: required physical evidence unavailable; claim remains unverified')
            else:result['evidence_state']='contradictory' if result['status']=='disagrees' else 'supporting'
            checks.append(result)
    verified=[c['agreement'] for c in checks if c['agreement'] is not None]
    neural=float(np.mean([o['neural_confidence'] for o in outputs])) if outputs else 0
    symbolic=float(np.mean(verified)) if verified else None
    coverage=len(verified)/max(total,1)
    temporal=next((o for o in outputs if o.get('temporal_evidence')), None)
    if temporal:
        # For temporal work, deterministic visible-change evidence is primary;
        # semantic claims are assessed separately and cannot borrow its support.
        visible=next((c['agreement'] for c in checks if c['claim'].get('type')=='visible_change' and c['agreement'] is not None), 0)
        trust = .4 * neural + .6 * (symbolic or 0) * coverage
        temporal_info = temporal['temporal_evidence']
        evidence_support = float(temporal_info.get('evidence_strength', 0))
        alignment_quality = temporal_info.get('alignment_quality', 'WARNING')
        if temporal_info.get('supported') and evidence_support > 0:
            align_mult = 1.0 if alignment_quality == 'GOOD' else 0.85 if alignment_quality == 'WARNING' else 0.5
            temp_trust = round(0.25 * neural + 0.75 * evidence_support * align_mult, 4)
            trust = max(trust, temp_trust)
    else:
        # Conservative score with missing evidence discounted; uncalibrated, not probability.
        trust=.4*neural+.6*(symbolic or 0)*coverage
        evidence_support=float(symbolic or 0)
        alignment_quality=None
    return {'trust_score':round(trust,4),'neural_confidence':neural,'symbolic_agreement':symbolic,
            'verification_coverage':coverage,'flags':list(dict.fromkeys(flags)),
            'checks':checks,'physical_statistics':stats,
            'unverified_claim_count':sum(c['status']=='unverified' for c in checks),
            'contradicted_claim_count':sum(c['status']=='disagrees' for c in checks),
            'evidence_support':round(evidence_support,4),'alignment_quality':alignment_quality,
            'method':'Evidence-derived claim score; model confidence is auxiliary and uncalibrated'}
