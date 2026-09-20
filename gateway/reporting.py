"""Escaped, self-contained HTML reports; JSON remains the audit source."""
import html
import json


def render_html(result):
    esc = lambda value: html.escape(str(value))
    def section(title, value):
        return f'<section class="report-section"><h2>{esc(title)}</h2><pre>{esc(json.dumps(value, indent=2, ensure_ascii=False))}</pre></section>'
    
    if result.get('analysis_report'):
        report = result['analysis_report']
        labels = ['Original image'] if result['scenario'] == 'SINGLE' else (['BEFORE', 'AFTER'] if result['scenario'] == 'BITEMPORAL_PAIR' else [i['modality'].upper() for i in result['input']['images']])
        previews = result.get('embedded_previews', result.get('previews', []))
        pictures = ''.join(f'<figure><img style="max-width:100%;max-height:440px" alt="{esc(labels[n])}" src="{esc(src)}"><figcaption>{esc(labels[n])}</figcaption></figure>' for n, src in enumerate(previews))
        overlay = result.get('overlay')
        if overlay and overlay.get('type') == 'bbox':
            source_id = overlay.get('image_id')
            n = next((i for i, image in enumerate(result['input']['images']) if image['id'] == source_id), 0)
            src = previews[n] if n < len(previews) else ''
            marks = ''.join(f'<rect x="{b["box"][0]}" y="{b["box"][1]}" width="{b["box"][2]-b["box"][0]}" height="{b["box"][3]-b["box"][1]}" fill="none" stroke="cyan" stroke-width="2"><title>{esc(b["label"])}</title></rect>' for b in overlay['data'])
            pictures += f'<h2>Candidate detector regions</h2><svg role="img" aria-label="Candidate detector regions" viewBox="0 0 {overlay["width"]} {overlay["height"]}"><image href="{esc(src)}" width="{overlay["width"]}" height="{overlay["height"]}"/>{marks}</svg>'
        return ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                '<title>SatQuery specialist report</title><style>body{font:16px/1.6 system-ui;max-width:1000px;margin:auto;padding:24px}pre{white-space:pre-wrap;overflow-wrap:anywhere}section{margin:24px 0}</style>'
                f'<h1>{esc(report["specialist"])} analysis</h1><p>Query: {esc(report["query"])}</p><h2>Direct answer</h2><p style="white-space:pre-wrap">{esc(report["answer"])}</p>'
                + pictures + ''.join(section(key.replace('_', ' ').title(), report[key]) for key in ('observations','spatial_evidence','evidence','uncertainty','confidence','execution_summary'))
                + section('Execution trace', result['execution_trace']) + '</html>')

    previews = result.get('embedded_previews', result.get('previews', []))
    pics = ''.join(f'<figure><img alt="Input preview" src="{esc(p)}"><figcaption>Input {n+1}</figcaption></figure>' for n, p in enumerate(previews))
    overlay = result.get('overlay'); svg = ''
    if overlay:
        marks = []
        first_pic = previews[0] if previews else ''
        if first_pic:
            marks.append(f'<image href="{esc(first_pic)}" x="0" y="0" width="{overlay["width"]}" height="{overlay["height"]}" preserveAspectRatio="none"/>')
        q_lower = (result.get('query') or '').lower()
        if overlay.get('type') == 'bbox':
            for item in overlay.get('data', []):
                x, y, x2, y2 = item['box']
                lbl = (item.get('label') or '').lower()
                target_combined = lbl + ' ' + q_lower
                if any(k in target_combined for k in ('build', 'urban', 'house', 'structure', 'infrastruct')):
                    stroke_col = '#f97316'
                    fill_col = 'rgba(249, 115, 22, 0.22)'
                    tag_bg = '#ea580c'
                elif any(k in target_combined for k in ('water', 'river', 'lake', 'sea', 'pond', 'ocean')):
                    stroke_col = '#38bdf8'
                    fill_col = 'rgba(56, 189, 248, 0.22)'
                    tag_bg = '#0284c7'
                elif any(k in target_combined for k in ('veg', 'tree', 'forest', 'green', 'agriculture')):
                    stroke_col = '#22c55e'
                    fill_col = 'rgba(34, 197, 94, 0.22)'
                    tag_bg = '#16a34a'
                else:
                    stroke_col = '#38bdf8'
                    fill_col = 'rgba(56, 189, 248, 0.22)'
                    tag_bg = '#0284c7'
                
                tag_w = max(70, len(item.get('label', '')) * 8 + 16)
                marks.append(f'<rect x="{x}" y="{y}" width="{x2-x}" height="{y2-y}" fill="{fill_col}" stroke="{stroke_col}" stroke-width="3" rx="3"/>')
                marks.append(f'<rect x="{x}" y="{max(0, y-22)}" width="{tag_w}" height="20" fill="{tag_bg}" rx="3"/>')
                marks.append(f'<text x="{x+6}" y="{max(14, y-7)}" fill="#ffffff" font-size="11" font-weight="bold" font-family="system-ui, sans-serif">{esc(item.get("label", ""))}</text>')
        elif overlay.get('type') == 'mask':
            rows = overlay.get('data', []); h = len(rows); w = len(rows[0]) if h else 1
            mask_col = 'rgba(249, 115, 22, 0.65)' if any(k in q_lower for k in ('build', 'urban', 'house')) else 'rgba(56, 189, 248, 0.65)'
            for y, row in enumerate(rows):
                for x, v in enumerate(row):
                    if v: marks.append(f'<rect x="{x*overlay["width"]/w}" y="{y*overlay["height"]/h}" width="{overlay["width"]/w}" height="{overlay["height"]/h}" fill="{mask_col}"/>')
        
        legend_html = '<div style="display:flex;justify-content:center;gap:18px;margin-top:10px;font-size:12px;color:#cbd5e1;font-weight:600"><span><i style="display:inline-block;width:10px;height:10px;background:#38bdf8;border-radius:2px;margin-right:5px"></i> Water / River</span><span><i style="display:inline-block;width:10px;height:10px;background:#22c55e;border-radius:2px;margin-right:5px"></i> Vegetation</span><span><i style="display:inline-block;width:10px;height:10px;background:#f97316;border-radius:2px;margin-right:5px"></i> Built-up / Buildings</span><span><i style="display:inline-block;width:10px;height:10px;background:#94a3b8;border-radius:2px;margin-right:5px"></i> Roads</span></div>'
        svg = f'<section class="report-section"><h2>🛰️ Annotated Satellite Observation & Markings</h2><svg role="img" aria-label="Annotated Satellite Observation" viewBox="0 0 {overlay["width"]} {overlay["height"]}" style="width:100%;max-height:480px;border-radius:8px;background:#000;display:block">' + ''.join(marks) + f'</svg>{legend_html}</section>'
    
    trust_score = result.get('trust_score') or 0
    score_pct = round(trust_score * 100)
    v_conf = result.get('visual_confidence') or result.get('confidence_breakdown', {}).get('neural') or trust_score or 0
    visual_pct = round(v_conf * 100)
    trust_class = 'high' if score_pct >= 70 else 'moderate' if score_pct >= 40 else 'low'
    decision_status = result.get('decision', {}).get('status', 'ANSWERED')

    exec_ans = result.get('executive_answer') or result.get('answer', '')
    inventory = result.get('scene_inventory')
    inv_html = ''
    if inventory:
        p_cards = ''.join(f'<div style="background:#0f172a;border-left:3px solid #10b981;border-radius:6px;padding:10px 14px;margin-bottom:8px"><div style="display:flex;justify-content:space-between;align-items:center"><span style="font-weight:600;color:#f1f5f9">{esc(item.get("icon", "✓"))} {esc(item["name"])}</span><span style="font-size:10px;background:#10b98122;color:#34d399;border:1px solid #10b98144;padding:2px 6px;border-radius:4px">{esc(item.get("badge", "Present"))}</span></div><div style="font-size:12px;color:#94a3b8;margin-top:4px">{esc(item["detail"])}</div></div>' for item in inventory.get('present', []))
        a_cards = ''.join(f'<div style="background:#0f172a;border-left:3px solid #64748b;border-radius:6px;padding:10px 14px;margin-bottom:8px"><div style="display:flex;justify-content:space-between;align-items:center"><span style="font-weight:600;color:#cbd5e1">{esc(item.get("icon", "✕"))} {esc(item["name"])}</span><span style="font-size:10px;background:#64748b22;color:#94a3b8;border:1px solid #64748b44;padding:2px 6px;border-radius:4px">{esc(item.get("badge", "Absent"))}</span></div><div style="font-size:12px;color:#94a3b8;margin-top:4px">{esc(item["detail"])}</div></div>' for item in inventory.get('absent', []))
        inv_html = (
            '<section class="report-section">'
            '<h2>🛰️ Scene Feature Inventory (Image Me Kya Hai / Kya Nahi Hai)</h2>'
            '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px">'
            f'<div><h3 style="font-size:13px;color:#10b981;text-transform:uppercase;margin:0 0 10px">✓ Detected In Image (Present)</h3>{p_cards or "<p style=\'color:#64748b;font-size:12px\'>None</p>"}</div>'
            f'<div><h3 style="font-size:13px;color:#94a3b8;text-transform:uppercase;margin:0 0 10px">✕ Not Detected / Absent</h3>{a_cards or "<p style=\'color:#64748b;font-size:12px\'>None</p>"}</div>'
            '</div></section>'
        )

    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>SatQuery AI Analysis Report · {esc(result["query_id"])}</title>'
        '<style>'
        ':root{--bg:#090d16;--card:#111827;--border:#1f2d40;--text:#f1f5f9;--muted:#94a3b8;--primary:#0284c7;--success:#10b981;--warn:#f59e0b}'
        'body{font:14px/1.6 system-ui,-apple-system,sans-serif;margin:0;padding:32px 24px;background:var(--bg);color:var(--text);max-width:1160px;margin:auto}'
        'header{display:flex;justify-content:space-between;align-items:flex-start;padding-bottom:20px;border-bottom:1px solid var(--border);margin-bottom:24px}'
        '.brand{font-size:20px;font-weight:700;letter-spacing:1px;color:#38bdf8}'
        '.meta-pills{display:flex;gap:10px;flex-wrap:wrap;margin-top:8px}'
        '.pill{display:inline-flex;align-items:center;padding:4px 10px;border-radius:16px;font-size:12px;font-weight:600;background:#1e293b;border:1px solid #334155;color:var(--text)}'
        '.pill.high{background:#10b98122;color:#10b981;border-color:#10b98144}'
        '.pill.moderate{background:#0284c722;color:#38bdf8;border-color:#0284c744}'
        '.pill.low{background:#f59e0b22;color:#f59e0b;border-color:#f59e0b44}'
        '.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin-bottom:24px}'
        '.kpi{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px}'
        '.kpi small{display:block;font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}'
        '.kpi strong{display:block;font-size:22px;margin-top:4px;color:#f8fafc}'
        '.report-section{background:var(--card);padding:22px;margin:18px 0;border:1px solid var(--border);border-radius:10px}'
        'h1{margin:0;font-size:24px}h2{font-size:16px;color:#38bdf8;margin:0 0 14px}'
        'p{margin:0 0 10px;color:#e2e8f0;font-size:15px}'
        '.previews-wrap{display:flex;gap:16px;flex-wrap:wrap;margin:14px 0}'
        'figure{margin:0;background:#0d1420;border:1px solid var(--border);border-radius:8px;padding:8px}'
        'figcaption{font-size:12px;color:var(--muted);margin-top:6px;text-align:center}'
        'img,svg{max-width:100%;max-height:440px;border-radius:6px;display:block}'
        'pre{white-space:pre-wrap;overflow-wrap:anywhere;font:11px/1.5 monospace;background:#0a0f18;padding:14px;border-radius:6px;color:#94a3b8;border:1px solid #1c2738;margin:0}'
        '.print-btn{background:#0284c7;color:#fff;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;font-weight:600;font-size:13px}'
        '.print-btn:hover{background:#0369a1}'
        '@media print{body{background:#fff;color:#000;padding:0}.report-section,.kpi{border-color:#ccc;background:#fff;color:#000}h2{color:#0284c7}.brand,.print-btn{display:none}pre{background:#f8f9fa;color:#111;border-color:#ddd}}'
        '</style></head><body>'
        '<header><div>'
        '<div class="brand">🛰️ SatQuery AI · Satellite Intelligence Report</div>'
        f'<div class="meta-pills">'
        f'<span class="pill">ID: {esc(result["query_id"][:12])}</span>'
        f'<span class="pill">Task: {esc(result.get("task", "SINGLE").upper())}</span>'
        f'<span class="pill {trust_class}">{score_pct}% Trust Score</span>'
        f'<span class="pill">Status: {esc(decision_status)}</span>'
        f'</div>'
        '</div>'
        '<button class="print-btn" onclick="window.print()">🖨️ Print / Save PDF</button>'
        '</header>'
        '<div class="kpi-grid">'
        f'<div class="kpi"><small>User Query</small><strong>{esc(result["query"])}</strong></div>'
        f'<div class="kpi"><small>AI Visual Accuracy</small><strong style="color:#38bdf8">{visual_pct}% Confidence</strong></div>'
        f'<div class="kpi"><small>Trust Score</small><strong style="color:var(--primary)">{score_pct}% [{trust_class.upper()}]</strong></div>'
        f'<div class="kpi"><small>Decision Gate</small><strong>{esc(decision_status)}</strong></div>'
        '</div>'
        f'<section class="report-section"><h2>Executive Satellite Interpretation</h2><p style="font-size:16px;font-weight:600;color:#38bdf8;margin-bottom:8px">Query: "{esc(result["query"])}"</p><p style="font-size:15px;line-height:1.6;color:#f8fafc">{esc(exec_ans)}</p></section>'
        f'{inv_html}'
        f'{svg if svg else f"<div class=\'previews-wrap\'>{pics}</div>"}'
        f"{section('Validation and input metadata', result['input'])}"
        f"{section('MODEL INFERENCE — unverified where indicated', result['specialists'])}"
        f"{section('MEASURED / PHYSICAL EVIDENCE — measurement proxies', result['verification'])}"
        f"{section('Trust and confidence', result.get('confidence_breakdown'))}"
        f"{section('Spatial measurements and GIS exports', result.get('spatial_products', []))}"
        f"{section('AUXILIARY CONTEXT — does not establish causality', result.get('context', {'status': 'Unavailable'}))}"
        f"{section('Limitations', result['limitations'])}"
        f"{section('Provenance', result.get('provenance', {}))}"
        f"{section('Execution trace', result['execution_trace'])}"
        '</body></html>'
    )
