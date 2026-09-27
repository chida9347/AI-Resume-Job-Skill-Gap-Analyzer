import React from 'react'
import { ArrowRight, Sparkles, Target } from 'lucide-react'

export default function ResumeSignals({ comparison, onInterview }) {
  const score = comparison.similarity_score
  return <aside className="insights-panel">
    <div className="panel-kicker">03 / SUMMARY</div><h2>Resume signals</h2>
    <div className="ats-score"><span>Job skills found in resume</span><b>{score}<small>%</small></b></div>
    <div className="signal-line"><span>{comparison.matched_skills.length} of {comparison.matched_skills.length + comparison.missing_skills.length} requested skills found</span><i><b style={{ width: `${score}%` }} /></i></div>
    <div className="insight-callout"><span className="callout-icon"><Sparkles size={15} /></span><div><b>What matches</b><p>{comparison.matched_skills.length ? `Highlight ${comparison.matched_skills.slice(0, 2).join(' and ')} near the top of your resume.` : 'Add relevant experience near the top, if you have it.'}</p></div></div>
    <div className="insight-callout callout-gap"><span className="callout-icon"><Target size={15} /></span><div><b>What to check</b><p>{comparison.missing_skills.length ? `Search your resume for ${comparison.missing_skills.slice(0, 2).join(' and ')}. Add them only if accurate.` : 'Make sure your relevant results are easy to find.'}</p></div></div>
    <button className="interview-link" onClick={onInterview}>Open all interview questions <ArrowRight size={16} /></button>
  </aside>
}