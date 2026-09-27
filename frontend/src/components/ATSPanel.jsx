import React from 'react'
import { AlertCircle, CheckCircle2, CircleHelp, FileCheck2, SearchCheck } from 'lucide-react'

function ScoreRing({ score }) {
  return <div className="ats-ring" style={{ '--score-angle': `${score * 3.6}deg` }} role="img" aria-label={`ATS simulation score ${score} out of 100`}>
    <div className="ats-ring-inner"><strong>{score}</strong><span>OUT OF 100</span></div>
  </div>
}

export default function ATSPanel({ result, loading, error }) {
  return <section className="advanced-card ats-card">
    <div className="advanced-card-heading"><div><span className="panel-kicker">04 / RECRUITER LENS</span><h2>ATS Simulation</h2></div><SearchCheck size={19} /></div>
    {loading && <div className="feature-state"><span className="loading-dot" /> Checking resume wording, sections, and formatting…</div>}
    {error && <div className="feature-error" role="alert"><AlertCircle size={15} /> {error}</div>}
    {!loading && !error && result && <>
      <div className="ats-summary"><ScoreRing score={result.ats_score} /><div className="ats-summary-copy"><b>Estimated ATS score</b><p>A guide based on words found, resume sections, and text layout. It is not a score from a real employer system.</p><div className="ats-subscore"><span>Job wording found</span><b>{result.keyword_match}%</b></div><div className="ats-subscore"><span>Text formatting</span><b>{result.formatting_quality}%</b></div></div></div>
      <div className="section-score-grid">{Object.entries(result.section_score).map(([name, score]) => <div className="section-score" key={name}><span>{name}</span><b>{score}%</b><i><em style={{ width: `${score}%` }} /></i></div>)}</div>
      <div className="keyword-block"><div className="feature-subheading"><span>Job words not found in resume</span><small>{result.missing_keywords.length}</small></div><div className="feature-tags">{result.missing_keywords.length ? result.missing_keywords.slice(0, 12).map((keyword) => <span className="feature-tag feature-tag-missing" key={keyword}>{keyword}</span>) : <span className="feature-empty">No missing keywords identified.</span>}</div></div>
      <div className="ats-feedback"><div className="feature-subheading"><span>Suggested fixes</span><CircleHelp size={14} /></div>{result.feedback.length ? result.feedback.slice(0, 6).map((item) => <p key={item}><FileCheck2 size={14} />{item.replace('Missing important keyword:', 'Job word not found in resume:')}</p>) : <p><CheckCircle2 size={14} />No immediate issues detected.</p>}</div>
    </>}
  </section>
}