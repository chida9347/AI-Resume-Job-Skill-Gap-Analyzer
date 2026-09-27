import React from 'react'
import { AlertCircle, ArrowRight, MessageCircleQuestion } from 'lucide-react'

export default function InterviewPreview({ tips, loading, error, onOpen }) {
  return <section className="interview-preview">
    <div className="interview-preview-heading">
      <div><span className="panel-kicker">04 / PREPARE</span><h2>Interview questions</h2><p>Use these to practice explaining your experience for this role.</p></div>
      <button className="button-secondary" onClick={onOpen}>View interview prep <ArrowRight size={15} /></button>
    </div>
    {loading && <div className="feature-state"><span className="loading-dot" /> Preparing role-specific questions…</div>}
    {error && <div className="feature-error" role="alert"><AlertCircle size={15} /> {error}</div>}
    {!loading && !error && tips?.questions?.length > 0 && <div className="interview-preview-list">
      {tips.questions.slice(0, 2).map((item, index) => <article className="interview-preview-item" key={item.question}>
        <span className="interview-preview-number">0{index + 1}</span>
        <div><h3>{item.question}</h3><p>{item.example_answer}</p></div>
        <MessageCircleQuestion size={17} />
      </article>)}
    </div>}
  </section>
}