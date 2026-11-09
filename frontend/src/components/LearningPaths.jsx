import React from 'react'
import { AlertCircle, ArrowUpRight, BookOpenCheck, Clock3, Lightbulb, Target } from 'lucide-react'

function RoadmapItem({ path, index }) {
  return (
    <details className="learning-item" open={index === 0}>
      <summary>
        <span className="learning-skill">
          <span className="learning-number">{String(index + 1).padStart(2, '0')}</span>
          {path.skill}
        </span>
        <span className="learning-duration"><Clock3 size={13} />{path.duration}</span>
      </summary>
      <div className="learning-detail">
        <div className="learning-meta">
          {path.requirement && <span className={`mini-badge ${path.requirement === 'required' ? 'is-required' : ''}`}>{path.requirement}</span>}
          {path.priority && <span className="mini-badge">{path.priority} priority</span>}
          {path.level && <span className="mini-badge">{path.level}</span>}
          {typeof path.progress === 'number' && <span className="mini-badge">{path.progress}% planned</span>}
        </div>
        <ol>
          {path.roadmap.map((step, stepIndex) => (
            <li key={step}><span>{stepIndex + 1}</span>{step}</li>
          ))}
        </ol>
        {path.objectives?.length > 0 && (
          <div className="learning-objectives">
            <b><Target size={13} /> Objectives</b>
            <ul>{path.objectives.map((item) => <li key={item}>{item}</li>)}</ul>
          </div>
        )}
        {path.project && (
          <div className="project-idea">
            <Lightbulb size={15} />
            <div><b>Try building</b><span>{path.project}</span></div>
            <ArrowUpRight size={14} />
          </div>
        )}
        {path.note && <p className="learning-note">{path.note}</p>}
      </div>
    </details>
  )
}

export default function LearningPaths({ paths, loading, error, hasGaps, title = 'Learning paths' }) {
  return (
    <section className="advanced-card learning-card">
      <div className="advanced-card-heading">
        <div><span className="panel-kicker">05 / BUILD THE GAP</span><h2>{title}</h2></div>
        <BookOpenCheck size={19} />
      </div>
      <p className="advanced-card-intro">Turn role gaps into small, practical learning goals. These are study suggestions, not endorsements of a course.</p>
      {loading && <div className="feature-state"><span className="loading-dot" /> Mapping skills to next steps…</div>}
      {error && <div className="feature-error" role="alert"><AlertCircle size={15} /> {error}</div>}
      {!loading && !error && !hasGaps && (
        <div className="feature-empty-state"><BookOpenCheck size={18} /> No skill gaps to map from this comparison.</div>
      )}
      {!loading && !error && hasGaps && paths?.length > 0 && (
        <div className="learning-list">
          {paths.map((path, index) => <RoadmapItem path={path} index={index} key={path.skill} />)}
        </div>
      )}
      {!loading && !error && hasGaps && !paths?.length && (
        <div className="feature-empty-state"><BookOpenCheck size={18} /> No roadmap could be generated for these gaps.</div>
      )}
    </section>
  )
}
