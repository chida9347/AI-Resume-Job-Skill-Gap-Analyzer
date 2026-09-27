import React from 'react'
import { AlertCircle, ArrowDownToLine, LoaderCircle, Sparkles } from 'lucide-react'

export default function ResumeRewrite({ result, loading, error, onApply, onDownload, applying }) {
  const hasChanges = result?.rewritten !== result?.original

  return <section className="advanced-card rewrite-card">
    <div className="advanced-card-heading"><div><span className="panel-kicker">06 / ROLE ALIGNMENT</span><h2>Resume Rewrite</h2></div><Sparkles size={19} /></div>
    <p className="advanced-card-intro">Review the draft before applying it to your editable resume.</p>
    {loading && <div className="feature-state"><LoaderCircle className="spin" size={16} /> Rewriting relevant experience…</div>}
    {error && <div className="feature-error" role="alert"><AlertCircle size={15} /> {error}</div>}
    {!loading && !error && result && <>
      <div className="rewrite-method"><span className="rewrite-method-dot" />{result.method === 'openai' ? 'AI-generated draft' : 'Rule-based draft'}</div>
      <div className="rewrite-comparison">
        <div className="rewrite-column"><h3>Before</h3><pre>{result.original}</pre></div>
        <div className="rewrite-column rewrite-after"><h3>After</h3><pre>{result.rewritten}</pre></div>
      </div>
      {!hasChanges && <p className="rewrite-noop">No text changes suggested.</p>}
      <p className="rewrite-caution">Check the draft for accuracy. PDF export uses extracted text and may not preserve the original layout.</p>
      <div className="rewrite-actions">
        <button className="button-primary apply-rewrite" onClick={onApply} disabled={applying || !hasChanges}>
          {applying && <LoaderCircle className="spin" size={15} />}
          <span>{applying ? 'Applying…' : hasChanges ? 'Apply Changes' : 'No changes to apply'}</span>
        </button>
        <button className="button-secondary download-rewrite" onClick={onDownload} disabled={!hasChanges}>
          <ArrowDownToLine size={16} /><span>Download rewrite draft PDF</span>
        </button>
      </div>
    </>}
  </section>
}