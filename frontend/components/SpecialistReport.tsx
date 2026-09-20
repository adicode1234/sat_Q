import { translateText, type AppLanguage } from "../routes/translations";

export type AnalysisReport = {
  query: string; task: string; specialist: string; answer: string;
  observations: Array<{text: string; image_ids: string[]; kind: string}>;
  spatial_evidence: unknown[];
  evidence: Record<string, Array<{text: string; image_ids: string[]; kind: string}>>;
  uncertainty: string[];
  confidence: {level: string | null; reason: string};
  execution_summary: Record<string, unknown>;
};

function renderPointWise(text: string, lang: AppLanguage = 'en') {
  if (!text) return null;
  // Split on bullets, (1)/(2), newlines, or numbered lists
  let points = text
    .split(/(?:\s*\(\d+\)\s*|\n\s*[•\-*]\s*|\n\s*\d+\.\s*|\n{2,})/)
    .map(p => p.trim().replace(/^[•\-*]\s*/, ''))
    .filter(p => p.length > 0);

  // If still single block, try splitting by newline or period with capital
  if (points.length === 1 && text.includes('\n')) {
    points = text.split('\n').map(p => p.trim().replace(/^[•\-*]\s*/, '')).filter(p => p.length > 0);
  }

  if (points.length > 1) {
    return (
      <ul style={{ margin: 0, paddingLeft: '18px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {points.map((pt, idx) => (
          <li key={idx} style={{ lineHeight: '1.65', fontSize: '14.5px', color: '#f8fafc' }}>
            {translateText(pt, lang)}
          </li>
        ))}
      </ul>
    );
  }
  return <p style={{ whiteSpace: 'pre-wrap', lineHeight: '1.65', fontSize: '15px', color: '#f8fafc', margin: 0 }}>{translateText(text, lang)}</p>;
}

export default function SpecialistReport({report, lang = 'en'}: {report: AnalysisReport; lang?: AppLanguage}) {
  const isCloudSpecialist = report.specialist?.toLowerCase().includes('cloud') || report.specialist?.toLowerCase().includes('openrouter');

  if (isCloudSpecialist) {
    const findingsLabel = lang === 'hi' ? '🎯 प्रत्यक्ष निष्कर्ष' : lang === 'bn' ? '🎯 সরাসরি ফলাফল' : '🎯 Direct Findings';
    return (
      <section className="analysis-summary" aria-label="SatQuery cloud report" style={{ padding: '4px 0' }}>
        <div style={{
          background: 'rgba(2, 132, 199, 0.08)',
          border: '1px solid rgba(2, 132, 199, 0.35)',
          borderRadius: '10px',
          padding: '16px 20px',
          marginBottom: '12px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <span style={{ fontSize: '12px', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
              {findingsLabel}
            </span>
          </div>
          {renderPointWise(report.answer, lang)}
        </div>
      </section>
    );
  }

  const directAnswerLabel = lang === 'hi' ? 'प्रत्यक्ष उत्तर' : lang === 'bn' ? 'সরাসরি উত্তর' : 'Direct answer';
  const obsLabel = lang === 'hi' ? 'अवलोकन' : lang === 'bn' ? 'পর্যবেক্ষণ' : 'Observations';
  const uncLabel = lang === 'hi' ? 'अनिश्चितताएँ एवं सीमाएँ' : lang === 'bn' ? 'অনিশ্চয়তা ও সীমাবদ্ধতা' : 'Uncertainties & Limitations';

  return <section className="analysis-summary" aria-label="SatQuery specialist report">
    <h2>{report.specialist} · {report.task.replaceAll('_', ' ')}</h2>
    <p><strong>{lang === 'hi' ? 'प्रश्न:' : lang === 'bn' ? 'অনুসন্ধান:' : 'Query:'}</strong> {translateText(report.query, lang)}</p>
    <div style={{ background: 'rgba(2, 132, 199, 0.08)', border: '1px solid rgba(2, 132, 199, 0.3)', borderRadius: '8px', padding: '12px 16px', margin: '12px 0' }}>
      <h3 style={{ margin: '0 0 6px', color: '#38bdf8', fontSize: '13px' }}>{directAnswerLabel}</h3>
      <p style={{ whiteSpace: 'pre-wrap', margin: 0, fontSize: '14.5px', color: '#f1f5f9' }}>{translateText(report.answer, lang)}</p>
    </div>
    {report.observations.length > 0 && (
      <div>
        <h3>{obsLabel}</h3>
        <ul>{report.observations.map((item, i) => <li key={i}>{translateText(item.text, lang)} ({item.kind}; {item.image_ids.join(', ')})</li>)}</ul>
      </div>
    )}
    {report.spatial_evidence.length > 0 && (
      <div>
        <h3>Visual / spatial evidence</h3>
        <pre style={{whiteSpace: "pre-wrap"}}>{JSON.stringify(report.spatial_evidence, null, 2)}</pre>
      </div>
    )}
    {Object.entries(report.evidence)
      .filter(([_, items]) => items && items.length > 0)
      .map(([key, items]) => <div key={key}>
        <h3>{key.toUpperCase()} evidence</h3>
        <ul>{items.map((item, i) => <li key={i}>{translateText(item.text, lang)} ({item.kind}; {item.image_ids.join(', ')})</li>)}</ul>
      </div>)}
    {report.uncertainty.length > 0 && (
      <details style={{ marginTop: '8px' }}>
        <summary style={{ cursor: 'pointer', color: '#94a3b8', fontSize: '12px' }}>{uncLabel} ({report.uncertainty.length})</summary>
        <ul style={{ marginTop: '6px' }}>{report.uncertainty.map((s, i) => <li key={i} style={{ color: '#cbd5e1', fontSize: '12px' }}>{translateText(s, lang)}</li>)}</ul>
      </details>
    )}
  </section>;
}
