import React from 'react'
import { Link } from 'react-router-dom'
import { BadgeCheck, Gauge, ShieldCheck, Target } from 'lucide-react'

const points = [
  { icon: Target, title: 'Evidence, not guesswork', body: 'See which skills your resume explicitly proves.' },
  { icon: Gauge, title: 'Explainable ATS estimate', body: 'Every point is broken down and capped honestly.' },
  { icon: ShieldCheck, title: 'Private by design', body: 'Your resume and history stay tied to your account.' },
]

export default function AuthLayout({ children }) {
  return (
    <div className="auth-shell">
      <aside className="auth-brand">
        <Link className="auth-brand-logo" to="/login" aria-label="Roleprint">
          <span className="auth-brand-mark"><Target size={21} strokeWidth={2.4} /></span>
          <span>roleprint<span className="auth-brand-period">.</span></span>
        </Link>

        <div className="auth-brand-copy">
          <span className="auth-eyebrow"><span /> RESUME INTELLIGENCE</span>
          <h1>Know what your resume <em>proves.</em></h1>
          <p>
            Compare your experience with a real job posting. Roleprint separates proven skills from
            related work and gaps, then shows you what to do next.
          </p>
          <ul className="auth-points">
            {points.map(({ icon: Icon, title, body }) => (
              <li key={title}>
                <span className="auth-point-icon"><Icon size={16} /></span>
                <span><b>{title}</b><small>{body}</small></span>
              </li>
            ))}
          </ul>
        </div>

        <div className="auth-brand-foot">
          <span><BadgeCheck size={14} /> No invented experience</span>
          <span>ROLEPRINT</span>
        </div>
      </aside>

      <main className="auth-panel">
        <div className="auth-card">{children}</div>
      </main>
    </div>
  )
}
