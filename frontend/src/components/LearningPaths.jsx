import React from 'react'
import { AlertCircle, ArrowUpRight, BookOpenCheck, Clock3, Lightbulb } from 'lucide-react'

export default function LearningPaths({ paths, loading, error, hasGaps }) {
  return <section className="advanced-card learning-card">
    <div className="advanced-card-heading"><div><span className="panel-kicker">05 / BUILD THE GAP</span><h2>Learning paths</h2></div><BookOpenCheck size={19} /></div>
    <p className="advanced-card-intro">Turn role gaps into small, practical learning goals.</p>
    {loading && <div className="feature-state"><span className="loading-dot" /> Mapping skills to next steps…</div>}
    {error && <div className="feature-error" role="alert"><AlertCircle size={15} /> {error}</div>}
    {!loading && !error && !hasGaps && <div className="feature-empty-state"><BookOpenCheck size={18} /> No skill gaps to map from this comparison.</div>}
    {!loading && !error && hasGaps && paths?.length > 0 && <div className="learning-list">{paths.map((path, index) => <details className="learning-item" key={path.skill} open={index === 0}>
      <summary><span className="learning-skill"><span className="learning-number">{String(index + 1).padStart(2, '0')}</span>{path.skill}</span><span className="learning-duration"><Clock3 size={13} />{path.duration}</span></summary>
      <div className="learning-detail"><ol>{path.roadmap.map((step, stepIndex) => <li key={step}><span>{stepIndex + 1}</span>{step}</li>)}</ol><div className="project-idea"><Lightbulb size={15} /><div><b>Try building</b><span>{path.project}</span></div><ArrowUpRight size={14} /></div></div>
    </details>)}</div>}
  </section>
}