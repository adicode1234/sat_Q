import { useEffect, useRef, useState } from 'react';
import { alignment, Help, percent } from './Presentation';

type Options = { modality?: string; date?: string; bands?: string[]; sar_units?: string; coregistered?: boolean; benchmark_source?: string };
type ImageInfo = { id: string; filename: string; bands: string[]; shape: number[]; crs: string | null; resolution_m: number | null;
  date: string | null; modality: string; calibration_state: string; suggested_modality: string; source_type: string;
  original_metadata?: { shape: number[] }; visual_only?: boolean; geospatial_measurements_allowed?: boolean;
  warnings?: string[]; preprocessing_steps?: { code: string; message: string }[];
  raster_metadata: { format: string; dtype: string[] }; quality: { score: number; warnings: string[] } };
type Overlay = { type: string; width: number; height: number; image_id: string; data: { box: number[]; label: string }[] };
type Measurement = { image_id: string; date: string | null; fraction: number | null; area_m2: number | null; measurement?: string; reason?: string };
export type Result = { query_id: string; query: string; answer: string; task: string; trust_score?: number; report_url: string; html_report_url?: string; geojson_url?: string;
  previews: string[]; overlay?: Overlay; input: { images: ImageInfo[]; validation_status: string; validation: unknown };
  decision?: { status: string; reason: string; needed: string | null }; trust_explanation?: string;
  confidence_breakdown: { input_quality?: number; consensus?: string; neural?: number | null; symbolic?: number | null; coverage?: number; evidence_support?: number; alignment_quality?: string }; context?: unknown;
  verification: { checks: { claim: { type: string; value?: string; subject?: string; direction?: string }; status: string; evidence?: string; agreement: number | null; reason?: string }[] };
  temporal_analysis?: { visible_change?: boolean; changed_fraction?: number; alignment_quality?: string; trust_label?: string; claims?: Result['verification']['checks'] };
  spatial_products?: { label: string; pixel_count: number; limitation?: string; geojson: { area_m2?: number; area_ha?: number; area_km2?: number; reason?: string } }[];
  specialists: { model?: string; status?: string; mode: string; measurements?: Measurement[]; trend?: { direction: string }; heatmap?: { semantics: string; data: (number | null)[][] } }[] };

const shown = (value: unknown) => value === null || value === undefined || value === '' ? 'Unavailable' : String(value);

type Validation = { warnings?: string[]; actions_taken?: { code: string; message: string }[]; blocking_errors?: { code: string; message: string }[]; message?: string; suggestion?: string; alignment?: { overlap_valid_fraction: number; alignment_class?: string }[] };

export function InputInspector({ files, options, scenario, query = '' }: { files: (File | undefined)[]; options: Options[]; scenario: string; query?: string }) {
  const [inspection, setInspection] = useState<{ images: ImageInfo[]; validation_status: string; validation: Validation } | null>(null);
  const [message, setMessage] = useState('');
  const generation = useRef(0);
  useEffect(() => { generation.current++; setInspection(null); setMessage(''); }, [files, options, scenario, query]);
  async function inspect() {
    const current = ++generation.current;
    setMessage('Inspecting raster content…');
    try {
      const body = new FormData(); files.filter((f): f is File => Boolean(f)).forEach(f => body.append('images', f));
      body.append('query', query); body.append('scenario', scenario); body.append('options', JSON.stringify(options.slice(0, files.length)));
      const response = await fetch('/api/inspect', { method: 'POST', body });
      const data = await response.json(); if (!response.ok) throw new Error(JSON.stringify(data.detail));
      if (current === generation.current) { setInspection(data); setMessage(''); }
    } catch (error) { if (current === generation.current) setMessage(error instanceof Error ? error.message : 'Inspection failed'); }
  }
  return <section className="inspection"><button type="button" onClick={inspect} disabled={!files.some(Boolean) || message === 'Inspecting raster content…'}>Inspect inputs before inference</button>
    <p role="status">{message || inspection?.validation_status.replaceAll('_', ' ')}</p>
    {inspection?.images.map(image => <article className="input-digest" key={image.id}><strong>{image.filename}</strong><p>{image.modality} · {image.bands.join(', ')} · {(image.original_metadata?.shape || image.shape).slice().reverse().join(' × ')}</p><p>{image.date || 'Acquisition date unavailable'}</p>{!!image.preprocessing_steps?.length && <p className="supports">✓ Automatically normalized</p>}<details><summary>Band mapping & provenance</summary><Metadata image={image}/></details></article>)}
    {inspection?.validation.actions_taken?.length ? <div><h4>Automatic fixes</h4><ul>{inspection.validation.actions_taken.map((step, n) => <li key={n}>{step.message}</li>)}</ul></div> : null}
    {inspection?.validation.warnings?.map((warning, n) => <p key={n}>{warning}</p>)}
    {inspection?.validation.blocking_errors?.map((error, n) => <p role="alert" key={n}>{error.message}</p>)}
    {inspection?.validation.suggestion && <p>{inspection.validation.suggestion}</p>}
    {inspection?.validation.alignment?.map((item, n) => <p key={n}>Shared valid overlap: {(item.overlap_valid_fraction * 100).toFixed(1)}% · Alignment: {item.alignment_class || 'Review needed'}</p>)}
    {inspection && <details><summary>Detailed validation and preprocessing audit</summary><pre>{JSON.stringify(inspection.validation, null, 2)}</pre></details>}
  </section>;
}

function Metadata({ image }: { image: ImageInfo }) {
  const rows = { Format: image.raster_metadata?.format, Dimensions: image.shape?.slice().reverse().join(' × '), 'Original dimensions': image.original_metadata?.shape.slice().reverse().join(' × '), Bands: image.bands?.join(', '),
    Dtype: image.raster_metadata?.dtype?.join(', '), CRS: image.crs, 'Approx. resolution (m)': image.resolution_m,
    'Acquisition date': image.date, Modality: image.modality, 'Suggested modality': image.suggested_modality,
    'Analysis mode': image.visual_only ? 'VISUAL-ONLY — pixel analysis available' : 'Geospatial', 'Physical area and coordinates': image.geospatial_measurements_allowed ? 'Available' : 'Disabled', Calibration: image.calibration_state === 'unknown' && image.modality === 'SAR' ? 'UNCALIBRATED SAR — relative visual analysis only' : image.calibration_state, Provenance: image.source_type };
  return <dl className="metadata-grid">{Object.entries(rows).map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{shown(value)}</dd></div>)}</dl>;
}

function ClaimCard({ check }: { check: Result['verification']['checks'][number] }) {
  const appearance = check.claim.type === 'visible_change' || check.claim.subject === 'appearance';
  const evidence = check.evidence === 'deterministic change mask' ? 'Change mask + pixel comparison' : check.evidence;
  return <article className={`finding-card ${check.status}`}><p className="summary-kicker">{check.status === 'supported' ? 'VERIFIED FINDING' : 'FINDING TO REVIEW'}</p><div><h3>{appearance ? 'Visible appearance change' : check.claim.subject || check.claim.type.replaceAll('_', ' ')}</h3><strong className="finding-status">{check.status.toUpperCase()}</strong></div>
    <dl><dt>Evidence</dt><dd>{evidence || check.reason || 'Independent evidence unavailable'}</dd><dt>Evidence agreement</dt><dd>{percent(check.agreement)}</dd><dt>Scope</dt><dd>{appearance ? 'Visual change only' : check.claim.direction || check.claim.value || 'Claim-specific evidence'}</dd></dl>
    {appearance && <p className="quiet">Exact semantic cause requires additional evidence.</p>}
  </article>;
}

function TemporalSummary({ result }: { result: Result }) {
  const temporal = result.temporal_analysis;
  if (!temporal) return <section className="analysis-summary"><h2>Analysis result</h2><p className="summary-lede">{result.answer}</p></section>;
  const checks = temporal.claims || result.verification.checks;
  const supported = checks.some(c => c.status === 'supported' && (c.claim.type === 'visible_change' || c.claim.subject === 'appearance'));
  const a = alignment(result);
  return <section className="analysis-summary" aria-labelledby="analysis-summary-title">
    <h2 id="analysis-summary-title">Temporal change summary</h2>
    <p className="summary-lede">{temporal.visible_change === true ? 'Visible appearance change detected.' : temporal.visible_change === false ? 'No visible appearance change detected.' : 'Visible change has not been assessed.'}</p>
    <div className="summary-metrics"><div><strong>{temporal.changed_fraction == null ? 'Not assessed' : `${(temporal.changed_fraction * 100).toFixed(1)}%`}</strong><span>Candidate visual change</span></div><div><strong>{percent(result.confidence_breakdown.symbolic)}</strong><span>Evidence agreement</span></div><div><strong className={a.raw === 'POOR' ? 'poor' : ''}>{a.label}</strong><span>Alignment <Help text="Quality of spatial correspondence between observations."/></span></div><div><strong>{result.trust_score == null ? 'Not assessed' : `${Math.round(result.trust_score * 100)} / 100`}</strong><span>Final trust</span></div></div>
    <p className="primary-finding"><strong>Primary finding</strong>{supported ? 'Visible change is supported by deterministic pixel evidence.' : 'Review the measured change and its claim-specific evidence below.'}</p>
    <p className="summary-note">{a.raw === 'WARNING' ? 'Residual alignment uncertainty remains. ' : a.raw === 'POOR' ? 'Poor alignment limits spatial conclusions. ' : ''}The appearance mask alone does not establish the semantic cause.</p>
  </section>;
}

export function EvidenceWorkspace({ result, busy, onJob, onResult }: { result: Result; busy: boolean; onJob: (id: string) => void; onResult: (result: Result) => void }) {
  const [limits, setLimits] = useState({ max_query_chars: 8000 });
  useEffect(() => { fetch('/api/config').then(r => r.json()).then(setLimits).catch(() => {}); }, []);
  const [tab, setTab] = useState('Summary'); const [box, setBox] = useState([0, 0, 32, 32]); const [query, setQuery] = useState('Measure water area in this region');
  const [message, setMessage] = useState(''); const [zoom, setZoom] = useState(1);
  useEffect(() => { const [h, w] = result.input.images[0].shape; setBox([0, 0, w, h]); setMessage(''); setZoom(1); }, [result.query_id]);
  async function followup() {
    setMessage('Starting region analysis…');
    try { const r = await fetch(`/api/jobs/${result.query_id}/followup`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query, box }) });
      const data = await r.json(); if (!r.ok) throw new Error(JSON.stringify(data.detail)); onJob(data.job_id); setMessage('');
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Follow-up failed'); }
  }
  async function context() {
    setMessage('Requesting rainfall context…');
    try { const r = await fetch(`/api/jobs/${result.query_id}/context`, { method: 'POST' }); const data = await r.json();
      if (!r.ok) throw new Error(JSON.stringify(data.detail)); onResult(data); setMessage('');
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Context unavailable'); }
  }
  const measurements = result.specialists.flatMap(s => s.measurements || []);
  return <section className="evidence-workspace"><TemporalSummary result={result}/><div className="tool-tabs" aria-label="Evidence sections">{['Summary', 'Evidence', 'Change map', 'Compare', 'Measurements', 'Region follow-up', 'Metadata', 'Exports'].map(name => <button type="button" key={name} aria-pressed={tab === name} onClick={() => setTab(name)}>{name}</button>)}</div>
    
    {tab === 'Summary' && <div className="claim-grid">{result.verification.checks.map((check, i) => <ClaimCard check={check} key={i}/>)}</div>}
    {tab === 'Metadata' && <><p className="analysis-id">Analysis ID: {result.query_id}</p>{result.input.images.map(i => <details key={i.id} open><summary>{i.filename}</summary><Metadata image={i}/></details>)}<details><summary>Input validation · {result.input.validation_status}</summary><pre>{JSON.stringify(result.input.validation, null, 2)}</pre></details></>}
    {(tab === 'Evidence' || tab === 'Change map') && <>{result.spatial_products?.length ? result.spatial_products.map((p, i) => <article key={i}><h3>{p.label}</h3><p>{p.pixel_count.toLocaleString()} selected pixels</p><p>{p.geojson.area_m2 == null ? p.geojson.reason : `${p.geojson.area_m2.toFixed(1)} m² · ${p.geojson.area_ha?.toFixed(3)} ha · ${p.geojson.area_km2?.toFixed(5)} km²`}</p><small>{p.limitation || 'Candidate-region measurement; not ground-truth land cover.'}</small></article>) : <p>No spatial region is available for this answer.</p>}
      {result.specialists.filter(s => s.heatmap).map((s, i) => <details key={i}><summary>Uncertainty / score heatmap</summary><p>{s.heatmap?.semantics}</p><Heatmap values={s.heatmap?.data || []}/></details>)}</>}
    {tab === 'Evidence' && <>{result.verification.checks.map((check, i) => <ClaimCard key={i} check={check}/>)}<button disabled={busy || message.startsWith('Requesting')} onClick={context}>Fetch optional rainfall context</button><p>Context is separate from observed evidence and does not establish causality.</p>{result.context != null && <pre>{JSON.stringify(result.context, null, 2)}</pre>}</>}
    {tab === 'Compare' && <><label>Linked zoom <input type="range" min="1" max="4" step="0.1" value={zoom} onChange={e => setZoom(Number(e.target.value))}/></label><div className="compare-grid">{result.previews.map((p, i) => <figure key={p}><div className="compare-scroll"><img style={{ width: `${zoom * 100}%`, maxWidth: 'none' }} src={p} alt={`Observation ${i + 1}`}/></div><figcaption>{result.input.images[i].modality} · {shown(result.input.images[i].date)}</figcaption></figure>)}</div><p>Zoom is linked; each image can be scrolled independently.</p></>}
    {tab === 'Measurements' && <>{measurements.length ? <><svg viewBox="0 0 500 180" role="img" aria-label="Measurement fraction over observation sequence"><polyline fill="none" stroke="#70f6d7" strokeWidth="3" points={measurements.map((m, i) => `${20 + i * 460 / Math.max(1, measurements.length - 1)},${160 - (m.fraction || 0) * 140}`).join(' ')}/></svg>{measurements.map(m => <p key={m.image_id}>{shown(m.date)}: {m.fraction == null ? 'Unavailable' : `${(m.fraction * 100).toFixed(1)}%`} · {m.measurement || m.reason}</p>)}</> : <p>Select the multi-date workflow with 3–20 dated observations (subject to deployment limits) to measure a trajectory.</p>}</>}
    {tab === 'Region follow-up' && <><p>Select a grounded box or enter a pixel AOI. Coordinates use the current source image grid.</p>
      {result.overlay?.type === 'bbox' && result.overlay.data.map((b, i) => <button type="button" key={i} onClick={() => setBox(b.box)}>{b.label} · region {i + 1}</button>)}
      <div className="roi-fields">{['Left', 'Top', 'Right', 'Bottom'].map((name, i) => <label key={name}>{name}<input type="number" min="0" value={box[i]} onChange={e => setBox(b => b.map((v, n) => n === i ? Number(e.target.value) : v))}/></label>)}</div>
      <label>Follow-up question<textarea value={query} onChange={e => setQuery(e.target.value)} maxLength={limits.max_query_chars}/></label><button disabled={busy || !query.trim() || message.startsWith('Starting')} onClick={followup}>Analyze selected region</button></>}
    {tab === 'Exports' && <div className="exports"><a href={result.report_url} download>JSON audit report</a>{result.html_report_url && <a href={result.html_report_url} download>Human-readable HTML report</a>}{result.geojson_url ? <a href={result.geojson_url} download>GeoJSON regions</a> : <p>GeoJSON unavailable: no georeferenced spatial output.</p>}</div>}
    <p role="status">{message}</p>
  </section>;
}

function Heatmap({ values }: { values: (number | null)[][] }) {
  const height = values.length, width = values[0]?.length || 1;
  return <svg className="score-heatmap" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Uncalibrated spatial score; brighter orange indicates higher values">{values.flatMap((row, y) => row.map((v, x) => v == null ? null : <rect key={`${x}-${y}`} x={x} y={y} width="1" height="1" fill={`rgb(${Math.round(v * 255)},${Math.round(v * 140)},30)`}/>))}</svg>;
}

type DatasetScore = { requested: number; completed: number; failed: number; splits: string[]; exact_match: number | null; token_f1: number | null };
export function BenchmarkDashboard() {
  const [data, setData] = useState<{ scope?: string; evaluation_date?: string; datasets: Record<string, DatasetScore>; models?: string[]; reason?: string } | null>(null);
  const [error, setError] = useState('');
  const refresh = () => fetch('/api/benchmarks').then(r => { if (!r.ok) throw new Error('Benchmark data unavailable'); return r.json(); }).then(setData).catch(e => setError(String(e)));
  useEffect(() => { refresh(); }, []);
  const rsvqa = data?.datasets?.RSVQA;
  const bounded = Object.entries(data?.datasets || {}).filter(([name]) => name !== 'RSVQA');
  return <details className="panel benchmark-panel" id="benchmarks"><summary><strong>Research validation</strong><span>Public evaluation available · Model benchmarks, separate from current analysis trust</span></summary><div className="benchmark-content"><button onClick={refresh}>Refresh saved results</button><p role="status">{error || data?.reason}</p>
    {rsvqa && <article className="official-benchmark"><h3>RSVQA · {rsvqa.splits.includes('official_test') && rsvqa.completed === rsvqa.requested ? 'FULL OFFICIAL TEST' : 'SAVED EVALUATION'}</h3><div className="benchmark-statistics"><p><strong>{rsvqa.completed.toLocaleString()} / {rsvqa.requested.toLocaleString()}</strong>questions processed</p><p><strong>{rsvqa.failed.toLocaleString()}</strong>pipeline failures</p><p><strong>{rsvqa.exact_match == null ? 'Unavailable' : `${(rsvqa.exact_match*100).toFixed(1)}%`}</strong>Answer Exact Match</p></div><p>Measures strict model answer matching; it is separate from SatQuery’s current evidence-derived trust score.</p></article>}
    {!!bounded.length && <section className="bounded-slices"><h3>Additional bounded smoke slices</h3>{bounded.map(([name,score]) => <article key={name}><h4>{name}</h4><p>N={score.requested} · execution smoke slice</p><details><summary>View scores</summary><p>Answer Exact Match: {score.exact_match == null ? 'Unavailable' : `${(score.exact_match*100).toFixed(1)}%`}</p><p>{score.completed} completed · {score.failed} pipeline failures</p><p>Too few samples for a representative benchmark conclusion.</p></details></article>)}</section>}
    <details><summary>Detailed metrics and methodology</summary><p>Evaluated: {shown(data?.evaluation_date)}</p><p>{data?.scope}</p>{Object.entries(data?.datasets || {}).map(([name,score]) => <p key={name}>{name} · Token F1: {score.token_f1 == null ? 'Unavailable' : score.token_f1.toFixed(3)} · Split: {score.splits.join(', ')}</p>)}<p>{data?.models?.join('; ')}</p><p>Execution completion is not accuracy. These evaluations do not establish SAC-domain validation.</p></details></div></details>;
}

export function AnalysisHistory({ onResult }: { onResult: (result: Result) => void }) {
  const [rows, setRows] = useState<{ query_id: string; query: string; task: string; timestamp: string; report_url: string }[]>([]);
  const [error, setError] = useState('');
  const refresh = () => fetch('/api/history').then(r => r.json()).then(setRows).catch(() => setError('History unavailable'));
  useEffect(() => { refresh(); }, []);
  async function open(url: string) { try { const r = await fetch(url); if (!r.ok) throw new Error(); onResult(await r.json()); } catch { setError('Saved report unavailable'); } }
  return <details className="history panel"><summary>Analysis history</summary><button onClick={refresh}>Refresh history</button><p role="status">{error}</p>{rows.map(row => <button key={row.query_id} onClick={() => open(row.report_url)}>{row.query} · {row.task} · {shown(row.timestamp)}</button>)}</details>;
}
