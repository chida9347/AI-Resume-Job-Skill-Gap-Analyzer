import React from 'react'
import { CircleHelp, Target } from 'lucide-react'

export default function SkillsSnapshot({ comparison }) {
  return <section className="result-panel skills-panel">
    <div className="panel-heading"><div><span className="panel-kicker">01 / SKILLS</span><h2>Skills snapshot</h2></div><Target size={19} /></div>
    <div className="skill-group"><h3><span className="status-dot dot-green" /> Found in both <span className="count-pill">{comparison.matched_skills.length}</span></h3><div className="skill-list">{comparison.matched_skills.length ? comparison.matched_skills.map((skill) => <span className="skill-tag tag-match" key={skill}>{skill}</span>) : <p className="empty-note">No requested skills were found in the resume text.</p>}</div></div>
    <div className="panel-divider" />
    <div className="skill-group"><h3><span className="status-dot dot-coral" /> Not found in resume <span className="count-pill">{comparison.missing_skills.length}</span></h3><div className="skill-list">{comparison.missing_skills.length ? comparison.missing_skills.map((skill) => <span className="skill-tag tag-missing" key={skill}>{skill}</span>) : <p className="empty-note">All detected job skills appear in the resume text.</p>}</div></div>
    <div className="panel-footnote"><CircleHelp size={14} /> This checks resume wording; it cannot tell whether you have an unlisted skill.</div>
  </section>
}