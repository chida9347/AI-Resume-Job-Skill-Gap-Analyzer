import React from 'react'
import { ArrowRight, Check, LoaderCircle, Sparkles } from 'lucide-react'

export default function SuggestionsPanel({ suggestions, selected, onToggle, onReview, updating, error }) {
  return <section className="result-panel suggestion-panel">
    <div className="panel-heading"><div><span className="panel-kicker">02 / NEXT STEPS</span><h2>Resume changes to consider</h2></div><Sparkles size={19} /></div>
    <p className="panel-intro">Check a skill only if you have it. Confirmed skills are added to your resume; other selections become review notes.</p>
    <div className="suggestion-list">{suggestions.length ? suggestions.map((suggestion) => <label key={suggestion.id} className={`suggestion-row ${selected.includes(suggestion.id) ? 'suggestion-selected' : ''}`}><input type="checkbox" checked={selected.includes(suggestion.id)} onChange={() => onToggle(suggestion.id)} /><span className="custom-check"><Check size={13} /></span><span className="suggestion-copy"><b>{suggestion.skill}</b><span>{suggestion.kind === 'skill' ? `I confirm I have ${suggestion.skill}; add it to my Skills section.` : suggestion.text}</span></span></label>) : <p className="empty-note">Nothing to add. Your skills align with the role.</p>}</div>
    {error && <p className="error-banner" role="alert">{error}</p>}
    <button className="button-secondary suggestion-action" onClick={onReview} disabled={updating || selected.length === 0}>{updating ? <><LoaderCircle className="spin" size={15} /> Updating…</> : <>Add selected skills &amp; review resume <ArrowRight size={16} /></>}</button>
  </section>
}