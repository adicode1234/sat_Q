import { useEffect, useState } from 'react';
import type { Result } from './AnalysisTools';

export const percent = (n: number | null | undefined) => n == null ? 'Not assessed' : `${Math.round(n * 100)}%`;
export const decisionLabel = (status?: string) => status === 'ANSWERED' ? 'ANALYSIS COMPLETE' : (status || 'Awaiting analysis').replaceAll('_', ' ');
export function alignment(result: Result) {
  const raw = result.confidence_breakdown.alignment_quality || result.temporal_analysis?.alignment_quality;
  const usable = result.input.validation_status !== 'INCOMPATIBLE';
  return { raw, label: raw === 'WARNING' && usable || raw === 'USABLE_WITH_CAVEAT' ? 'Usable' : raw === 'GOOD' ? 'Good' : raw === 'POOR' ? 'Poor' : raw || 'Not assessed' };
}
const help = {
  trust: 'Evidence-derived assessment of how defensible the conclusion is. It is not a probability of accuracy.',
  support: 'Strength of independent evidence supporting the current claim.',
  coverage: 'How much of the required evidence could be checked.',
  input: 'Image usability, not answer accuracy.',
  model: 'Auxiliary neural score; not necessarily calibrated. It must not be read as a probability of correctness.',
  alignment: 'Quality of spatial correspondence between observations.',
};
export function Help({ text }: { text: string }) {
  return <span className="help" tabIndex={0} aria-label={text}>?<span role="tooltip">{text}</span></span>;
}
export function TrustPanel({ result }: { result: Result | null }) {
  if (!result) return <section className="trust panel"><h2>Final trust</h2><p className="quiet">Run an analysis to assess the evidence.</p></section>;
  const c = result.confidence_breakdown, a = alignment(result);
  const supported = result.verification.checks.some(v => v.status === 'supported');
  const deterministic = result.verification.checks.some(v => /deterministic.*change|pixel comparison/i.test(v.evidence || ''));
  const limits = [
    ...(a.raw === 'WARNING' ? ['Residual alignment uncertainty'] : a.raw === 'POOR' ? ['Poor spatial alignment — localization is unreliable'] : []),
    ...(c.neural != null ? ['Auxiliary model score is uncalibrated'] : []),
    ...(result.temporal_analysis ? ['Exact semantic cause is not independently verified by the appearance mask'] : []),
    ...(c.coverage != null && c.coverage < 1 ? ['Some claim evidence could not be checked'] : []),
    ...(c.consensus === 'disagreement' ? ['Evidence channels disagree'] : []),
  ];
  const metric = (label: string, value: string, tooltip: string) => <div className="trust-metric"><span>{label} <Help text={tooltip}/></span><strong>{value}</strong></div>;
  return <section className="trust panel" aria-label="Trust assessment">
    <h2>FINAL TRUST <Help text={help.trust}/></h2>
    <div className="final-score">{result.trust_score == null ? 'Not assessed' : Math.round(result.trust_score * 100)}<small> / 100</small></div>
    {result.temporal_analysis?.trust_label && <strong className="trust-level">{result.temporal_analysis.trust_label} TRUST</strong>}
    <p className="quiet">{supported ? 'Evidence-supported result' : 'Evidence assessment available'}</p>
    <p className={`decision-status ${result.decision?.status === 'ANSWERED' ? 'complete' : ''}`}>{decisionLabel(result.decision?.status)}</p>
    {metric('Evidence support', percent(c.evidence_support), help.support)}
    {metric('Evidence coverage', percent(c.coverage), help.coverage)}
    {metric('Input quality', percent(c.input_quality), help.input)}
    {metric('Evidence agreement', percent(c.symbolic), 'Agreement between the claim and independently checkable evidence.')}
    {metric('Alignment', a.label, help.alignment)}
    {a.raw === 'WARNING' && <p className="quiet alignment-note">Residual alignment uncertainty <Help text="Images passed bounded alignment checks but residual registration uncertainty remains. Review spatial evidence for precise localization."/></p>}
    <div className="why-trust"><h3>Why this trust score?</h3><h4>Supports trust</h4><ul className="supports">
      {c.input_quality != null && c.input_quality >= .5 && <li>{percent(c.input_quality)} input usability</li>}
      {c.coverage != null && c.coverage > 0 && <li>{percent(c.coverage)} evidence coverage</li>}
      {deterministic && <li>Deterministic change evidence available</li>}
      {c.consensus === 'agreement' && <li>Checked claim and evidence agree</li>}
      {!supported && !deterministic && <li className="quiet">Independent support is not yet established</li>}
    </ul><h4>Limits trust</h4><ul className="limits">{limits.map(l => <li key={l}>{l}</li>)}{!limits.length && <li>Scores remain uncalibrated; review the claim-specific scope</li>}</ul></div>
    <div className="auxiliary"><span>MODEL SCORE <Help text={help.model}/></span><strong>{c.neural == null ? 'Not used' : percent(c.neural)}</strong><p>{c.neural == null ? 'No neural score contributed to this result' : 'Auxiliary · uncalibrated'}</p></div>
    <p className="quiet trust-footnote">Trust is evidence-derived, not a calibrated probability.</p>
    <details className="trust-method"><summary>How trust is calculated</summary><p>{result.trust_explanation}</p><p>{result.decision?.reason}</p><p>{result.decision?.needed}</p><p>Raw alignment value: {a.raw || 'Unavailable'}</p><pre>{JSON.stringify(c, null, 2)}</pre></details>
  </section>;
}

type Event = { step: number; action: string; model?: string; status?: string; result?: unknown };
const stages: [string, string[]][] = [
  ['Validate inputs', ['validation_complete']], ['Normalize images', ['automatic_preprocessing']],
  ['Detect intent', ['classify_intent']], ['Specialist analysis', ['model_complete']],
  ['Verify claims', ['verification_complete']], ['Evidence consensus', ['consensus']],
  ['Trust assessment', ['answer_gate']], ['Prepare result', ['report']],
];
const modelNames: Record<string, string> = { temporal_analysis_v1: 'Temporal analysis', change_mask_v1: 'Change detection', change_vqa_v1: 'Change VQA', grounding_v1: 'Grounding', vqa_caption_v1: 'Scene VQA / captioning', fusion_optical_sar_v1: 'Optical + SAR fusion', measurement_v1: 'Measurement' };
export function TraceOverview({ events, result, busy }: { events: Event[]; result: Result | null; busy: boolean }) {
  const used = result?.specialists.filter(s => s.status !== 'failed' && s.status !== 'unavailable') || [];
  return <section className="trace panel" id="execution-trace"><h2>Analysis team</h2>
    {result ? <><p>{used.length} specialist{used.length === 1 ? '' : 's'} contributed</p><ul className="team-list">{used.map((s, n) => <li key={n}>{modelNames[s.model || ''] || s.model || s.mode}</li>)}{events.some(e => e.action === 'verification_complete') && <li>Independent verification stage</li>}</ul></> : <p className="quiet">{busy ? 'Specialists are working' : 'Stages appear as the mission runs'}</p>}
    <ol className="stage-list" aria-live="polite">{stages.filter(([, actions]) => actions.some(a => events.some(e => e.action === a))).map(([label]) => <li key={label}><span aria-hidden="true">✓</span>{label}</li>)}</ol>
    {events.some(e => e.action === 'error' || e.action === 'model_failure') && <p role="alert">An execution issue was recorded. Review the full trace.</p>}
    <details className="full-trace"><summary>View full execution trace · {events.length} events</summary>{events.map(e => <details key={e.step}><summary>{e.action.replaceAll('_', ' ')}</summary><pre>{JSON.stringify(e, null, 2)}</pre></details>)}</details>
  </section>;
}

export function ObservationViewport({ result }: { result: Result }) {
  const temporal = result.input.images.length === 2 && !!result.temporal_analysis;
  const [mode, setMode] = useState('COMPARE'), [index, setIndex] = useState(0), [opacity, setOpacity] = useState(.4);
  useEffect(() => { setMode(temporal ? 'COMPARE' : 'ORIGINAL'); setIndex(0); setOpacity(.4); }, [result.query_id, temporal]);
  const overlayIndex = result.input.images.findIndex(i => i.id === result.overlay?.image_id);
  const selected = mode === 'AFTER' ? 1 : mode === 'EVIDENCE' ? Math.max(0, overlayIndex) : index;
  const buttonLabels: Record<string, string> = {
    ORIGINAL: '🖼️ Natural View',
    EVIDENCE: '🎯 AI Highlights',
    BEFORE: '◀️ Before Image',
    AFTER: '▶️ After Image',
    COMPARE: '↔️ Side-by-Side Compare',
  };
  function scene(n: number, evidence = false) {
    const image = result.input.images[n], o = evidence ? result.overlay : undefined;
    return <figure key={n}><div className="scene-frame"><img src={result.previews[n]} alt={`${temporal ? n ? 'After' : 'Before' : 'Observation'}: ${image.filename}`}/>
      {o && <svg className="evidence-overlay" viewBox={`0 0 ${o.width} ${o.height}`} preserveAspectRatio="none" aria-label="Candidate evidence overlay">{o.type === 'mask' ? (o.data as unknown as number[][]).map((row,y) => row.map((v,x) => v ? <rect key={`${x}-${y}`} x={x*o.width/row.length} y={y*o.height/(o.data.length)} width={o.width/row.length+.2} height={o.height/o.data.length+.2} fill="#ff974b" opacity={opacity}/> : null)) : o.data.map((b,n) => (
        <g key={n}>
          <rect x={b.box[0]} y={b.box[1]} width={b.box[2]-b.box[0]} height={b.box[3]-b.box[1]} fill="#38bdf8" fillOpacity={opacity/2} stroke="#38bdf8" strokeWidth="2.5" rx="3"/>
          <rect x={b.box[0]} y={Math.max(0, b.box[1] - 22)} width={Math.max(64, (b.label?.length || 4) * 9 + 14)} height="20" fill="#0284c7" rx="3"/>
          <text x={b.box[0] + 6} y={Math.max(14, b.box[1] - 7)} fill="#ffffff" fontSize="12" fontWeight="600" fontFamily="system-ui, sans-serif">{b.label}</text>
        </g>
      ))}</svg>}
    </div><figcaption><strong>{temporal ? n ? 'AFTER' : 'BEFORE' : image.modality}</strong> {image.date || 'Acquisition date unavailable'}<span>{image.filename}</span></figcaption></figure>;
  }
  return <div className="mission-viewer"><div className="view-modes" aria-label="Observation view">{(temporal ? ['BEFORE','AFTER','COMPARE','EVIDENCE'] : ['ORIGINAL','EVIDENCE']).map(m => <button key={m} disabled={m === 'EVIDENCE' && !result.overlay} aria-pressed={mode === m} onClick={() => {setMode(m);if(m==='BEFORE')setIndex(0);}}>{buttonLabels[m] || m}</button>)}</div>
    {!temporal && result.previews.length > 1 && <select aria-label="Observation" value={index} onChange={e => setIndex(Number(e.target.value))}>{result.input.images.map((i,n) => <option key={i.id} value={n}>{i.modality} · {i.date || i.filename}</option>)}</select>}
    <div className={mode === 'COMPARE' ? 'scene-compare' : 'scene-single'}>{mode === 'COMPARE' && temporal ? [scene(0),scene(1)] : scene(selected,mode === 'EVIDENCE')}</div>
    {mode === 'EVIDENCE' && <div className="overlay-legend"><span><i/> {result.overlay?.type === 'mask' ? 'Candidate appearance change' : 'Identified regions & bounding boxes'}</span><Help text="Visual evidence detected by AI specialist models."/><label>Overlay Opacity <input aria-label="Evidence overlay opacity" type="range" min=".1" max=".8" step=".05" value={opacity} onChange={e => setOpacity(Number(e.target.value))}/>{Math.round(opacity*100)}%</label></div>}
  </div>;
}
