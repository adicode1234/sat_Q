def combine(outputs, verification):
    answer='\n\n'.join(o['answer'] for o in outputs)
    flags=list(verification['flags'])
    for o in outputs:
        if o.get('cross_modal_disagreement'):
            flags.append('Optical/SAR disagreement: independently trained water experts disagree; inspect acquisition conditions.')
        if 'sar_water_proxy' in o:
            optical=o.get('fractions',{}).get('water'); sar=o['sar_water_proxy']
            if optical is None:continue
            if abs(optical-sar)>.2:
                flag=f'Optical/SAR disagreement: optical water candidate {optical:.0%}, SAR smooth-surface proxy {sar:.0%}.'
                flags.append(flag)
                if (o.get('cloud_proxy') or 0)>.2:
                    answer+='\n\nBright neutral pixels suggest possible cloud: SAR evidence receives more weight, but smooth returns cannot prove water.'
                else: answer+='\n\nOptical and SAR disagree. The available evidence cannot resolve the water claim.'
    if flags:answer+='\n\nVerification: '+ ' '.join(flags)
    return {'answer':answer,'short_answer':next((o.get('short_answer') or o.get('raw_vqa') for o in outputs if o.get('short_answer') or o.get('raw_vqa')),None),'overlay':next((o['overlay'] for o in reversed(outputs) if o.get('overlay')),None),
            'flags':list(dict.fromkeys(flags))}
