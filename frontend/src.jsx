import SpecialistReport from './components/SpecialistReport';
import React,{useEffect,useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {Satellite,Orbit,Layers,Upload,ArrowUpRight,ScanLine,Activity,ChevronRight,Download,Check,AlertTriangle,Radio,Globe2,LoaderCircle,Eye,EyeOff,Terminal,FileImage,X} from 'lucide-react';
import './style.css';
import './completion.css';
import './judge-polish.css';
import './user-friendly.css';
import './routes/styles.css';
import SatVisionNexus from './routes/index';
const MODES=[['SINGLE','Single image'],['CROSS_MODAL_PAIR','Optical + SAR'],['BITEMPORAL_PAIR','Before / after']];
const pct=v=>v===null||v===undefined?'—':`${Math.round(v*100)}%`;
function Overlay({overlay,visible}){if(!overlay||!visible)return null;return <svg className="evidence-overlay" viewBox={`0 0 ${overlay.width} ${overlay.height}`} preserveAspectRatio="none" aria-label="Analysis evidence overlay">{overlay.type==='bbox'?overlay.data.map((d,i)=><g key={i}><rect x={d.box[0]} y={d.box[1]} width={d.box[2]-d.box[0]} height={d.box[3]-d.box[1]} fill="#52e2c31a" stroke="#70f6d7" strokeWidth="2"/><text x={d.box[0]+5} y={Math.max(14,d.box[1]+14)} fill="#fff" fontSize="12">{d.label}</text></g>):overlay.data.map((row,y)=>row.map((v,x)=>v?<rect key={`${x}-${y}`} x={x*overlay.width/row.length} y={y*overlay.height/overlay.data.length} width={overlay.width/row.length+.2} height={overlay.height/overlay.data.length+.2} fill="#ff974b" fillOpacity=".6"/>:null))}</svg>}
function App(){
 const [scenario,setScenario]=useState('SINGLE'),[files,setFiles]=useState([]),[opts,setOpts]=useState([{modality:'optical'},{modality:'SAR',sar_units:'db'}]),[query,setQuery]=useState(''),[demos,setDemos]=useState([]),[result,setResult]=useState(null),[events,setEvents]=useState([]),[busy,setBusy]=useState(false),[error,setError]=useState(''),[health,setHealth]=useState(null),[view,setView]=useState(0),[showOverlay,setShowOverlay]=useState(true),[tab,setTab]=useState('answer'),[demoName,setDemoName]=useState(''),[jobId,setJobId]=useState(null);
 const socket=useRef(null),timer=useRef(null),polling=useRef(false),actions=useRef(null);
 actions.current={launch,demos,result,busy};
 useEffect(()=>{const context=document.modelContext;if(!context?.registerTool)return;const lifecycle=new AbortController();const specs=[{name:'satquery_read_analysis',description:'Read the current visible SatQuery result and its confidence breakdown.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true,untrustedContentHint:true},execute:()=>({busy:actions.current.busy,result:actions.current.result?{query_id:actions.current.result.query_id,task:actions.current.result.task,answer:actions.current.result.answer,confidence_breakdown:actions.current.result.confidence_breakdown,trust_score:actions.current.result.trust_score,trace_events:actions.current.result.execution_trace.length}:null})},{name:'satquery_start_demo',description:'Run one synthetic demo mission through the production pipeline and display its result.',inputSchema:{type:'object',properties:{id:{type:'string',enum:['vqa','grounding','change','fusion']}},required:['id'],additionalProperties:false},annotations:{readOnlyHint:false,untrustedContentHint:false},execute:async input=>{if(actions.current.busy)throw Error('Analysis already running');const d=actions.current.demos.find(d=>d.id===input?.id);if(!d)throw Error('Unknown demo');return {job_id:await actions.current.launch(d)}}}];for(const spec of specs){try{Promise.resolve(context.registerTool(spec,{signal:lifecycle.signal})).catch(()=>{})}catch{}}return()=>lifecycle.abort()},[]);
 useEffect(()=>{fetch('/api/demos').then(r=>r.json()).then(setDemos).catch(()=>{});fetch('/api/health').then(r=>r.json()).then(setHealth).catch(()=>{});return()=>{socket.current?.close();clearTimeout(timer.current)}},[]);
 function finish(data){setResult(data);setBusy(false);setView(data.overlay?.image_id==='img2'?1:0);setEvents(data.execution_trace);clearTimeout(timer.current);polling.current=false}
 async function monitor(id){setJobId(id);let terminal=false;const scheme=location.protocol==='https:'?'wss':'ws';const ws=new WebSocket(`${scheme}://${location.host}/api/trace/${id}`);socket.current=ws;
  async function poll(){if(terminal||polling.current)return;polling.current=true;try{const r=await fetch(`/api/jobs/${id}`);if(!r.ok)throw Error('Unable to read analysis status');const j=await r.json();setEvents(j.events);if(j.status==='complete'){terminal=true;finish(j.result)}else if(j.status==='failed'){terminal=true;setError(j.error);setBusy(false)}else timer.current=setTimeout(()=>{polling.current=false;poll()},1000)}catch(e){setError(e.message);setBusy(false)}finally{polling.current=false}}
  ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.type==='trace')setEvents(v=>v.some(x=>x.step===m.event.step)?v:[...v,m.event]);if(m.type==='complete'){terminal=true;finish(m.result)}if(m.type==='failed'){terminal=true;setError(m.error);setBusy(false)}};
  ws.onclose=()=>{if(!terminal)poll()};ws.onerror=()=>ws.close();
 }
 async function launch(demo){setError('');setBusy(true);setResult(null);setEvents([]);setTab('answer');setShowOverlay(true);socket.current?.close();clearTimeout(timer.current);
  try{let response;if(demo){setScenario(demo.scenario);setOpts([...demo.options,...(demo.options.length===1?[{modality:'optical'}]:[])]);setFiles([]);setQuery(demo.query);setDemoName(demo.title);response=await fetch(`/api/demos/${demo.id}`,{method:'POST'})}else{setDemoName('');const count=scenario==='SINGLE'?1:2;if(files.slice(0,count).filter(Boolean).length!==count)throw Error(`Select ${count} image${count>1?'s':''} first.`);const body=new FormData();files.slice(0,count).forEach(f=>body.append('images',f));body.append('scenario',scenario);body.append('query',query);body.append('options',JSON.stringify(opts.slice(0,count)));response=await fetch('/api/jobs',{method:'POST',body})}const data=await response.json();if(!response.ok)throw Error(typeof data.detail==='string'?data.detail:JSON.stringify(data.detail));monitor(data.job_id);return data.job_id}catch(e){setError(e.message);setBusy(false)}
 }
 function changeMode(mode){setScenario(mode);setResult(null);setDemoName('');setFiles([]);setOpts([{modality:'optical'},{modality:mode==='CROSS_MODAL_PAIR'?'SAR':'optical',sar_units:'db'}]);setEvents([]);setError('')}
 function updateOpt(i,key,value){setOpts(v=>v.map((o,n)=>n===i?{...o,[key]:value}:o))}
 const activeOverlay=result?.overlay&&result.overlay.image_id===`img${view+1}`?result.overlay:null;
 return <div className="app-shell">
  <aside className="rail"><a className="brand-symbol" href="#workspace" aria-label="SatQuery workspace"><Orbit size={30}/></a><div className="rail-nav"><a href="#workspace" className="rail-active" title="Analysis workspace"><Layers/></a><a href="#demo-missions" title="Demo missions"><Satellite/></a><a href="#execution-trace" title="Execution trace"><Activity/></a></div><span className="rail-coordinate">EARTH • OBSERVATION</span><Globe2 size={22}/></aside>
  <div className="app-body"><header className="topbar"><div className="wordmark">SATQUERY<span>AI</span><small>MISSION WORKSPACE</small></div><div className="header-meta"><span className="status-light"/>{health?'Gateway connected':'Connecting…'}<span className="tricolor"><i/><i/><i/></span></div></header>
  <main id="workspace"><div className="page-heading"><div><div className="eyebrow">REMOTE SENSING / INTELLIGENT ANALYSIS</div><h1>A clearer view of Earth<span>.</span></h1><p>Ask a question. Follow the evidence.</p></div><div className="mission-id"><Satellite size={28}/><div>MISSION CONTROL<small>Optical · SAR · Temporal</small></div></div></div>
   <div className="workspace-grid">
    <section className="inputs panel"><div className="section-title"><span className="section-number">01</span><h2>Set your observation</h2></div><div className="mode-tabs" role="tablist" aria-label="Input scenario">{MODES.map(([id,label])=><button role="tab" aria-selected={scenario===id} className={scenario===id?'selected':''} onClick={()=>changeMode(id)} disabled={busy} key={id}>{label}</button>)}</div>
     <div className="upload-list">{Array.from({length:scenario==='SINGLE'?1:2},(_,i)=><div className="image-entry" key={i}><label className={`dropzone ${files[i]?'has-file':''}`} onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();if(!busy){const f=e.dataTransfer.files[0];setFiles(v=>{const a=[...v];a[i]=f;return a})}}}><input type="file" accept=".tif,.tiff,.png,.jpg,.jpeg" disabled={busy} onChange={e=>setFiles(v=>{const a=[...v];a[i]=e.target.files[0];return a})}/><div className="upload-icon">{files[i]?<FileImage size={24}/>:<Upload size={24}/>}</div><strong>{files[i]?files[i].name:`${i===0?'Primary':'Companion'} image`}</strong><span>{files[i]?`${(files[i].size/1024/1024).toFixed(2)} MB · Click to replace`:'Drop imagery here or browse files'}</span><small>GEOTIFF / TIFF · UP TO 32 MB</small></label><div className="field-row"><label>Modality<select disabled={busy} value={opts[i]?.modality||'optical'} onChange={e=>updateOpt(i,'modality',e.target.value)}><option value="optical">Optical</option><option value="SAR">SAR</option></select></label>{scenario==='BITEMPORAL_PAIR'&&<label>Acquired<input type="date" disabled={busy} value={opts[i]?.date||''} onChange={e=>updateOpt(i,'date',e.target.value)}/></label>}</div><details><summary>Band mapping & provenance</summary><label>Band order <span>(optional for tagged TIFF)</span><input placeholder="red,green,blue,nir,swir" disabled={busy} onChange={e=>updateOpt(i,'bands',e.target.value?e.target.value.split(',').map(s=>s.trim()):undefined)}/></label>{opts[i]?.modality==='SAR'&&<label>SAR units<select value={opts[i]?.sar_units||'unknown'} disabled={busy} onChange={e=>updateOpt(i,'sar_units',e.target.value)}><option value="unknown">Unknown / uncalibrated</option><option value="db">Calibrated dB</option><option value="linear">Calibrated linear power</option></select></label>}<label>Public benchmark source <span>(required for PNG/JPEG)</span><input placeholder="Dataset name or source URL" disabled={busy} onChange={e=>updateOpt(i,'benchmark_source',e.target.value)}/></label>{scenario!=='SINGLE'&&<label className="checkbox"><input type="checkbox" disabled={busy} checked={!!opts[i]?.coregistered} onChange={e=>updateOpt(i,'coregistered',e.target.checked)}/>Benchmark pair is co-registered</label>}</details></div>)}</div>
     <form onSubmit={e=>{e.preventDefault();launch()}}><label className="query-label" htmlFor="query">What would you like to know?</label><textarea id="query" required maxLength={2000} disabled={busy} value={query} onChange={e=>setQuery(e.target.value)} placeholder="e.g. Where is surface water, and does the spectral evidence agree?"/><button className="run-button" disabled={busy} type="submit">{busy?<LoaderCircle className="spin" size={18}/>:<ScanLine size={18}/>} {busy?'Analyzing observation…':'Run analysis'}<ArrowUpRight size={18}/></button></form><p className="input-note">RGB benchmark images are supported. Spectral checks need the relevant bands.</p>
    </section>
    <section className="observation panel"><div className="section-title"><span className="section-number">02</span><h2>Observation viewport</h2><span className="mini-label">{result?result.scenario.replaceAll('_',' '):'AWAITING IMAGERY'}</span></div><div className="viewport-toolbar"><span><span className="tiny-dot"/>{demoName?'SYNTHETIC DEMO':result?'UPLOADED OBSERVATION':'IMAGE EXPLORER'}</span><button onClick={()=>setShowOverlay(!showOverlay)} disabled={!activeOverlay} aria-pressed={showOverlay}>{showOverlay?<Eye size={15}/>:<EyeOff size={15}/>} Evidence</button></div>
     <div className={`image-viewport ${result?'loaded':''}`}>
      {result?<div className="image-frame"><img src={result.previews[view]} alt={`Analysis input ${view+1}${demoName?' — synthetic fixture':''}`}/><Overlay overlay={activeOverlay} visible={showOverlay}/></div>:<div className="viewport-empty"><div className="orbit-grid"><Orbit size={86} strokeWidth={.8}/><Satellite size={33}/></div><h3>{busy?'Reading the observation':'Ready for your next observation'}</h3><p>{busy?'Specialists are gathering evidence. Follow the live trace.':'Upload an image or choose a demo mission below.'}</p><span className="view-crosshair tl">+</span><span className="view-crosshair tr">+</span><span className="view-crosshair bl">+</span><span className="view-crosshair br">+</span></div>}
      {busy&&<div className="scan-indicator"/>}
     </div><div className="viewport-footer">{result?.previews.length>1?<div className="image-switch">{result.previews.map((_,i)=><button className={view===i?'active':''} key={i} onClick={()=>setView(i)}>{result.input.images[i].modality} · {result.input.images[i].date||`Image ${i+1}`}</button>)}</div>:<span>{result?`${result.input.images[0].shape.join(' × ')} pixels`:'No image selected'}</span>}<span>{result?.input.metadata.crs||'CRS —'}</span></div>
     <div className="results-area"><div className="result-tabs"><button onClick={()=>setTab('answer')} className={tab==='answer'?'active':''}>Analysis</button><button onClick={()=>setTab('physical')} className={tab==='physical'?'active':''}>Physical evidence</button>{result&&<a className="report-link" href={result.report_url} download><Download size={15}/> JSON report</a>}</div>{error&&<div className="error" role="alert"><AlertTriangle size={18}/>{error}</div>}
      {!result?<div className="result-empty"><Radio size={20}/><p>{error?'Resolve the input issue and try again.':'Evidence-grounded findings will appear here.'}</p></div>:tab==='answer' && result.analysis_report?<SpecialistReport report={result.analysis_report}/>:tab==='answer'?<div className="answer"><div className="answer-meta"><span className="answer-tag">{result.task}</span><span>{result.specialists.length} specialist{result.specialists.length>1?'s':''} executed</span></div><p>{result.answer}</p><details><summary>Model modes & limitations</summary>{result.specialists.map((s,i)=><p key={i}>{s.mode}</p>)}{result.limitations.map(l=><p key={l}>{l}</p>)}</details></div>:<div className="physical-evidence">{Object.entries(result.verification.physical_statistics).map(([id,stats])=><div key={id}><h3>{id.toUpperCase()}</h3>{Object.entries(stats).map(([name,value])=><div className="physical-row" key={name}><span>{name}</span><span>{value.unavailable||('mean' in value?`${value.mean?.toFixed(3)??'Unavailable'} · valid ${pct(value.valid_fraction)}`:`${value.mean_db?.toFixed(1)??'—'} dB · dark ${pct(value.dark_fraction)}`)}</span></div>)}</div>)}<p className="input-note">Thresholds are proxies. Land-cover truth cannot be established by a single index.</p></div>}
     </div>
    </section>
    <aside className="evidence-column"><section className="trust panel"><div className="section-title"><span className="section-number">03</span><h2>Trust assessment</h2></div><div className="trust-score"><div className="score-ring" style={{'--score':`${(result?.trust_score||0)*360}deg`}}><span>{result?.trust_score == null ? '—' : Math.round(result.trust_score*100)}<small>/ 100</small></span></div><div><strong>{result?'Evidence assessed':'Awaiting analysis'}</strong><p>Neural + symbolic<br/>confidence</p></div></div><div className="score-row"><span>Specialist confidence</span><strong>{pct(result?.confidence_breakdown.neural)}</strong></div><div className="meter"><i style={{width:`${(result?.confidence_breakdown.neural||0)*100}%`}}/></div><div className="score-row"><span>Symbolic agreement</span><strong>{pct(result?.confidence_breakdown.symbolic)}</strong></div><div className="meter symbolic"><i style={{width:`${(result?.confidence_breakdown.symbolic||0)*100}%`}}/></div><div className="coverage"><span>Evidence coverage</span><span>{pct(result?.confidence_breakdown.coverage)}</span></div><p className="score-note">Uncalibrated research score. Missing physical evidence reduces trust.</p></section>
     <section id="execution-trace" className="trace panel"><div className="section-title"><Terminal size={17}/><h2>Execution trace</h2><span className={busy?'live active':'live'}>{busy?'LIVE':`${events.length} EVENTS`}</span></div><div className="trace-list" aria-live="polite">{events.length?events.map((e,i)=><details className="trace-event" key={e.step}><summary><span className={`event-icon ${e.action==='error'?'failed':''}`}>{e.action==='error'?<X size={13}/>:<Check size={13}/>}</span><span><strong>{e.action.replaceAll('_',' ')}</strong><small>{e.model|| (typeof e.result==='string'?e.result:e.reason||'Evidence recorded')}</small></span><ChevronRight size={13}/></summary><pre>{JSON.stringify(e,null,2)}</pre></details>):<div className="trace-empty"><Activity size={27}/><p>Every decision, in view.</p><span>Validation, model selection and verification appear as they happen.</span></div>}</div></section>
    </aside>
   </div>
   <section className="demos" id="demo-missions"><div className="demos-heading"><h2>Start with a demo mission</h2><span>Synthetic imagery · Real pipeline execution</span></div><div className="demo-grid">{demos.map((d,i)=><button key={d.id} disabled={busy} onClick={()=>launch(d)} className="demo-card"><span className="demo-icon">{i===0?<Globe2/>:i===1?<ScanLine/>:i===2?<Layers/>:<Satellite/>}</span><span><small>MISSION 0{i+1}</small><strong>{d.title}</strong><em>{d.label}</em></span><ArrowUpRight size={18}/></button>)}</div></section>
   <footer><span><Orbit size={15}/> SATQUERY AI <i>/</i> Remote-sensing research workspace</span><span>Inspired by Indian space exploration · Not affiliated with ISRO</span></footer>
  </main></div></div>
}
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo);
    this.setState({ errorInfo });
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '30px', color: '#ff9a42', background: '#090e16', minHeight: '100vh', fontFamily: 'monospace' }}>
          <h2 style={{ color: '#ff4d4f', fontSize: '20px', marginBottom: '10px' }}>⚠️ Component Error Detected</h2>
          <p style={{ color: '#eaf5ff', marginBottom: '15px' }}>{this.state.error?.toString()}</p>
          <pre style={{ background: '#020d1a', padding: '15px', borderRadius: '6px', overflow: 'auto', maxHeight: '300px', border: '1px solid #12395d' }}>
            {this.state.error?.stack || this.state.errorInfo?.componentStack}
          </pre>
          <button
            type="button"
            onClick={() => { this.setState({ hasError: false }); this.props.onFallback && this.props.onFallback(); }}
            style={{ marginTop: '20px', background: '#ff8c29', color: '#17120d', border: 'none', borderRadius: '4px', padding: '10px 18px', fontWeight: 'bold', cursor: 'pointer' }}
          >
            Switch to Classic Workspace Mode
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function RootApp() {
  const [view, setView] = useState('nexus');

  if (view === 'nexus') {
    return (
      <ErrorBoundary onFallback={() => setView('classic')}>
        <SatVisionNexus onSwitchView={() => setView('classic')} />
      </ErrorBoundary>
    );
  }

  return (
    <div>
      <div style={{ background: '#020d1a', borderBottom: '1px solid #12395d', padding: '8px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ color: '#ff8c29', fontWeight: 'bold', fontSize: '13px' }}>🔬 Classic Research Workspace</span>
        <button
          type="button"
          onClick={() => setView('nexus')}
          style={{ background: '#ff8c29', color: '#17120d', border: 'none', borderRadius: '4px', padding: '6px 12px', fontWeight: 'bold', fontSize: '12px', cursor: 'pointer' }}
        >
          ← Return to New SatQuery Portal
        </button>
      </div>
      <App />
    </div>
  );
}

createRoot(document.getElementById('root')).render(<RootApp />);
