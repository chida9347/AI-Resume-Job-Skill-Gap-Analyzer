import React from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  BadgeCheck,
  CheckCheck,
  FileText,
  Fingerprint,
  Gauge,
  Sparkles,
  Target,
} from 'lucide-react'

const features = [
  {
    icon: Target,
    title: 'Skill-by-skill evidence',
    body: 'See which requirements are explicitly demonstrated, merely mentioned, implied by related work, or missing entirely.',
  },
  {
    icon: Gauge,
    title: 'Explainable ATS estimate',
    body: 'Every point is broken down by required coverage, keyword relevance, sections and readability. No misleading perfect scores.',
  },
  {
    icon: Fingerprint,
    title: 'Private by design',
    body: 'Anonymous analysis works without an account. Sign in only when you want saved history and account controls.',
  },
]

export default function LandingPage() {
  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <div className="eyebrow"><span className="eyebrow-line" /> AI RESUME ANALYZER</div>
          <h1>AI Resume<br /><span>Analyzer.</span></h1>
          <p className="hero-lede">Optimize your resume for any job in seconds.</p>
          <Link className="button-primary hero-cta" to="/analyze">Analyze Resume <ArrowRight size={17} /></Link>
          <div className="hero-proof">
            <span><CheckCheck size={15} /> Skill-by-skill match</span><i />
            <span><FileText size={15} /> Your data stays yours</span>
          </div>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="visual-orbit orbit-one" /><div className="visual-orbit orbit-two" />
          <div className="visual-paper">
            <div className="paper-top">
              <span className="paper-avatar">JD</span>
              <div><b>Jordan Davis</b><span>PRODUCT DESIGNER</span></div>
              <BadgeCheck size={17} className="verified-icon" />
            </div>
            <div className="paper-rule" /><div className="paper-label">YOUR EXPERIENCE, AT A GLANCE</div>
            <div className="paper-skill-row"><span>Product strategy</span><span className="mini-match">MATCH</span></div>
            <div className="paper-skill-row"><span>Design systems</span><span className="mini-match">MATCH</span></div>
            <div className="paper-skill-row"><span>Data storytelling</span><span className="mini-gap">EXPLORE</span></div>
            <div className="paper-meter">
              <div className="meter-copy"><span>ROLE ALIGNMENT</span><b>78%</b></div>
              <div className="meter-track"><i /></div>
            </div>
            <div className="paper-note"><Sparkles size={14} /><span>A clearer picture of what to highlight.</span></div>
          </div>
          <div className="float-stamp stamp-match"><span className="stamp-dot" /> Good alignment</div>
          <div className="float-stamp stamp-skill"><span className="stamp-plus">+</span> Skill insight</div>
          <div className="visual-caption">YOUR NEXT CHAPTER, IN FOCUS <span>01 / 04</span></div>
        </div>
        <div className="hero-bottom">
          <span>BUILT FOR THE IN-BETWEEN</span><span>Know what fits. See what’s next.</span><ArrowRight size={16} />
        </div>
      </section>

      <section className="home-features" aria-label="What Roleprint does">
        {features.map(({ icon: Icon, title, body }) => (
          <article className="home-feature" key={title}>
            <span className="home-feature-icon"><Icon size={20} /></span>
            <h2>{title}</h2>
            <p>{body}</p>
          </article>
        ))}
      </section>

      <section className="home-band">
        <div>
          <div className="eyebrow"><span className="eyebrow-line" /> START WHERE YOU ARE</div>
          <h2>One resume. Any role.<br /><span>A clearer next step.</span></h2>
        </div>
        <div className="home-band-actions">
          <Link className="button-primary" to="/analyze">Analyze a resume <ArrowRight size={17} /></Link>
          <Link className="button-secondary" to="/register">Save your history</Link>
          <p>No API key or model download required. Semantic matching is optional and local-only.</p>
        </div>
      </section>
    </>
  )
}
