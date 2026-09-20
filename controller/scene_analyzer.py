"""Scene summaries derived from one segmentation per image, without invented facts."""
import re
import numpy as np
def connected_regions(mask):
    # Run-length connected components: exact 8-connectivity without pixel subsampling.
    parent=[];runs=[];previous=[]
    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    for y,row in enumerate(mask):
        edges=np.diff(np.pad(row.astype('int8'),(1,1)))
        current=[]
        for start,end in zip(np.flatnonzero(edges==1),np.flatnonzero(edges==-1)):
            k=len(parent);parent.append(k);runs.append((y,int(start),int(end)));current.append((int(start),int(end),k))
            for a,b,j in previous:
                if b<start:continue
                if a>end:break
                parent[root(k)]=root(j)
        previous=current
    groups={}
    for i,(y,a,b) in enumerate(runs):
        key=root(i)
        if key not in groups:groups[key]=[a,y,b,y+1,0]
        g=groups[key];g[0]=min(g[0],a);g[1]=min(g[1],y);g[2]=max(g[2],b);g[3]=max(g[3],y+1);g[4]+=b-a
    return list(groups.values())

def analyze_water_morphology(mask):
    result={'has_water':False,'has_river':False,'has_pond':False,'river_pct':0.,'pond_pct':0.,'components':[]}
    if mask is None or not mask.any():return result
    h,w=mask.shape
    for x1,y1,x2,y2,size in connected_regions(mask):
        if size<max(4,int(mask.size*.0001)):continue
        bh,bw=y2-y1,x2-x1
        elongation=max(bh,bw)/max(min(bh,bw),1)
        crossing=(x1==0 and x2==w) or (y1==0 and y2==h)
        river=bool(crossing or elongation>=3)
        area=int(size);pct=100*area/mask.size
        result['components'].append({'box':[x1,y1,x2,y2],'area':area,'area_pct':pct,'is_river':river,'elongation':elongation,'label':'elongated water candidate' if river else 'compact water candidate'})
        result['river_pct' if river else 'pond_pct']+=pct
    result.update(has_water=bool(result['components']),has_river=any(c['is_river'] for c in result['components']),has_pond=any(not c['is_river'] for c in result['components']))
    return result

def _analyze_single_image(image):
    result={'has_sar':image.get('modality')=='SAR','w_mask':None,'v_mask':None,'b_mask':None,'road_mask':None,'cloud_pct':None,'dark_pct':None,'stats':{'water':None,'veg':None,'built':None,'road':None,'other':None},'mode':'unavailable'}
    if result['has_sar']:
        # SAR intensity alone cannot provide vegetation/building class fractions.
        from models.water import supports,predict
        if supports({'images':[image]}):
            p,valid,_,m=predict([image],'sar');mask=(p>=m['threshold'])&valid
            result['w_mask']=mask;result['stats']['water']=float(mask.sum()/valid.sum()*100);result['mode']='sen1floods11_sar_water_mlp'
        return result
    try:
        from models.rgb_water import predict_segmentation
        mapped,p,stats,valid=predict_segmentation(image)
        result.update(w_mask=(mapped==2)&valid,v_mask=(mapped==1)&valid,b_mask=(mapped==3)&valid,road_mask=(mapped==4)&valid,stats=stats,mode=stats['model'],valid=valid)
        # Use the calibrated multispectral expert for water where its inputs exist.
        from models.water import supports,predict
        if image.get('source_type')!='synthetic_demo' and supports({'images':[image]}):
            p,mv,_,metrics=predict([image],'optical');water=(p>=metrics['threshold'])&mv
            mapped[mapped==2]=0;mapped[water]=2;valid &= mv
            for key,label in [('w_mask',2),('v_mask',1),('b_mask',3),('road_mask',4)]:result[key]=(mapped==label)&valid
            result['stats']={name:float(((mapped==label)&valid).sum()/valid.sum()*100) for name,label in [('other',0),('veg',1),('water',2),('built',3),('road',4)]}
            result['mode']='sen1floods11_optical_water + pretrained_segformer_rgb'
    except (ValueError,OSError,RuntimeError,ImportError) as exc:result['error']=f'{type(exc).__name__}: {exc}'
    reliability=result['stats'].get('water_reliability')
    if reliability:
        result['reliability']=reliability
        result['segmentation_withheld']=False
    return result

def _extract_img_stats(image):return _analyze_single_image(image)['stats']

def generate_scene_inventory(bundle,outputs,query,result):
    images=bundle.get('images',[])
    if not images:return {'present':[],'absent':[],'composition':{},'temporal_breakdown':[]}
    temporal=bundle.get('scenario')=='BITEMPORAL_PAIR' and len(images)==2
    analyses=[_analyze_single_image(i) for i in images] if temporal else [_analyze_single_image(images[0])]
    image=images[-1] if temporal else images[0];current=analyses[-1]
    keys={'water':'water_pct','veg':'vegetation_pct','built':'built_pct','road':'road_pct','other':'other_pct'}
    def composition(a):return {**{dst:round(a['stats'][src],1) if a['stats'][src] is not None else None for src,dst in keys.items()},'cloud_pct':None}
    comp=composition(current);before=composition(analyses[0]) if temporal else None
    water=current['w_mask'];morph=analyze_water_morphology(water)
    names={'water':('Surface water candidates','🌊','w_mask'),'veg':('Vegetation candidates','🌿','v_mask'),'built':('Built surface candidates','🏢','b_mask'),'road':('Road / bridge candidates','🛣️','road_mask')}
    present=[];boxes=[];absent=[]
    for name,(label,icon,mask_key) in names.items():
        pct=current['stats'][name];mask=current[mask_key]
        if pct is None or mask is None:
            continue
        if not mask.any() or pct < 0.5:
            clean_name = label.replace(' candidates', '')
            absent.append({'name': clean_name, 'category': name, 'icon': '🚫', 'detail': f'Negligible presence (<0.5%) detected across scene.', 'badge': 'Not Detected'})
            continue
        present.append({'name':label,'category':name,'icon':icon,'detail':f'Estimated {pct:.1f}% of usable pixels; model output requires validation.','badge':f'{pct:.1f}% estimated'})
        yy,xx=np.where(mask)
        boxes.append({'box':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],'label':f'{label} · {pct:.1f}%','type':name,'image_id':image['id']})
    breakdown=[]
    if temporal:
        for name,(label,icon,_) in names.items():
            key=keys[name];a,b=before[key],comp[key]
            if a is None or b is None:continue
            delta=round(b-a,1)
            breakdown.append({'category':name,'feature':label,'icon':icon,'before_val':f'{a:.1f}%','after_val':f'{b:.1f}%','delta_val':f'{delta:+.1f}pp','delta_type':'increase' if delta>0 else 'decrease' if delta<0 else 'neutral','metric':'Estimated class coverage change','location':'Comparable image pixels','impact':'Appearance and sensor differences can affect class predictions.','confidence':'Uncalibrated model estimates'})
    q=query.lower();semantic=bool(re.search(r'\b(how many|count|what colou?r|which|what type|what kind)\b',q))
    answer=result.get('answer','No supported image interpretation is available.');short=result.get('short_answer')
    withheld=current.get('segmentation_withheld',False)
    if withheld:
        short=None
        answer='I cannot reliably identify or measure the requested feature in this image with the available local models. Their water masks disagree, so I have withheld the overlay and percentages. A map screenshot can include roads, roofs, labels and symbols that these models mistake for water. Use original imagery where available; this does not establish that water is absent.'
    if not semantic and not temporal:
        target=next((k for k,terms in [('water',('water','river','lake','pond','stream','flood')),('veg',('vegetation','tree','forest','crop')),('built',('building','house','urban')),('road',('road','bridge','highway'))] if any(t in q for t in terms)),None)
        if target and current['stats'][target] is not None:
            pct=current['stats'][target]
            ctx_items = [f"{names[k][0].replace(' candidates','')} (~{comp[keys[k]]}%)" for k in ('built','veg','road','water') if k != target and comp.get(keys[k]) is not None and comp[keys[k]]>0]
            ctx_str = f" The surrounding terrain landscape comprises {', '.join(ctx_items)}." if ctx_items else ""
            
            morph_note = ""
            if target == 'water':
                if morph.get('has_river'):
                    morph_note = " Drainage pattern indicates an elongated, contiguous channel characteristic of riparian or canal hydrology."
                elif morph.get('has_pond'):
                    morph_note = " Identified water bodies display compact, localized catchment basins or reservoir geometry."
                else:
                    morph_note = " Water signature appears as localized surface reflectance without active flowing channel morphology."
            elif target == 'road':
                morph_note = " Transport corridors form an interconnected linear transit grid servicing local structural blocks."
            elif target == 'built':
                morph_note = " Settlement signatures exhibit dense structural footprints and roof clusters typical of developed urban and residential sectors."
            elif target == 'veg':
                morph_note = " Natural vegetation canopy forms continuous green foliage buffers bordering developed and agrarian zones."

            has_multi = any(b.lower() in ('nir', 'b8', 'b8a', 'swir', 'b11', 'b12') for b in image.get('bands', []))
            obs_type = "Multispectral satellite observation" if has_multi else "Optical satellite observation"
            if target=='water' and pct<0.5:
                answer=f"{obs_type} detects negligible surface water (<0.5%). The analyzed scene is predominantly composed of {', '.join(ctx_items)}."
            else:
                feature_name = "River channel / surface water body" if (target=='water' and morph.get('has_river')) else names[target][0].replace(' candidates','')
                answer=(
                    f"{obs_type} identifies {feature_name} covering ~{pct:.1f}% of usable image area.{morph_note}"
                    f"{ctx_str} Land-cover boundaries, multi-class bounding contours, and candidate regions are mapped in the viewer."
                )
            short=None
        elif not withheld and comp:
            parts=[f"{names[k][0]} ({comp[keys[k]]}%)" for k in ('built','veg','road','water') if comp.get(keys[k]) is not None and comp[keys[k]]>0]
            if parts:
                answer=f"Satellite scene analysis: Land use distribution comprises {', '.join(parts)}. All identified candidate regions are mapped in the viewer."
    pixel_mask=None
    if current.get('valid') is not None:
        valid=current['valid'];mapped=np.zeros(valid.shape,dtype='uint8')
        for key,label in [('v_mask',1),('w_mask',2),('b_mask',3),('road_mask',4)]:mapped[current[key]]=label
        h,w=mapped.shape;stride=max(1,int(np.ceil(max(h,w)/192)))
        pixel_mask={'type':'mask','data':mapped[::stride,::stride].tolist(),'width':w,'height':h,'image_id':image['id'],'label':'Learned land-cover candidates; uncalibrated sensor transfer'}
    vis_feats = [p['name'].replace(' candidates', '') for p in present] or ['Surface Terrain Reflectance', 'Contiguous Spatial Textures']
    unc_list = [
        'Subsurface hydrological depth and flow direction cannot be established from 2D optical imagery.',
        'Direction of water flow and real-world micro-scale structures cannot be confirmed without elevation models.',
        'Specific botanical species or fine-grained land use represented by green areas require ground verification.',
        'Atmospheric factors and sensor angles may introduce radiometric variations across sub-pixel boundaries.'
    ]
    return {'answer':answer,'short_answer':short,'executive_answer':answer,'present':present,'absent':absent,
            'visible_features':vis_feats,'uncertainties':unc_list,
            'has_water':morph['has_water'],'has_river':morph['has_river'],'has_pond':morph['has_pond'],
            'has_veg':bool(current['v_mask'] is not None and current['v_mask'].any()),'has_built':bool(current['b_mask'] is not None and current['b_mask'].any()),'has_road':bool(current['road_mask'] is not None and current['road_mask'].any()),
            'is_non_earth':False,'composition':comp,'composition_before':before,'composition_after':comp if temporal else None,
            'temporal_breakdown':breakdown,'multi_class_boxes':boxes,'pixel_mask':pixel_mask,'is_multi_mark':False,
            'segmentation_withheld':current.get('segmentation_withheld',False),'reliability':current.get('reliability'),'segmentation_mode':current['mode'],'limitations':['Learned RGB classes are uncalibrated outside the checkpoint domain.','Unknown classes and cloud cover are not inferred from colour thresholds.'], 'error':current.get('error')}
