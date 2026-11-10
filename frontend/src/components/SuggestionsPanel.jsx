import React, { useState } from 'react'
import { ArrowRight, Check, ChevronDown, LoaderCircle, Sparkles } from 'lucide-react'

export default function SuggestionsPanel({
  suggestions,
  selected,
  onToggle,
  onReview,
  updating,
  error,
  disabled = false,
  maxVisible = 3,
}) {
  const [expanded, setExpanded] = useState(false)
  const visible = expanded ? suggestions : suggestions.slice(0, maxVisible)
  const hiddenCount = Math.max(0, suggestions.length - maxVisible)

  return (
    <section className="result-panel suggestion-panel">
      <div className="panel-heading">
        <div><span className="panel-kicker">NEXT STEPS</span><h2>Close the gaps</h2></div>
        <Sparkles size={19} />
      </div>
      <p className="panel-intro">
        Check a skill only if you can genuinely support it. Confirmed skills are added to your resume; other selections become review notes.
      </p>
      <div className="suggestion-list">
        {visible.length ? visible.map((suggestion) => (
          <label
            key={suggestion.id}
            className={`suggestion-row ${selected.includes(suggestion.id) ? 'suggestion-selected' : ''}`}
          >
            <input type="checkbox" checked={selected.includes(suggestion.id)} onChange={() => onToggle(suggestion.id)} />
            <span className="custom-check"><Check size={13} /></span>
            <span className="suggestion-copy">
              <span className="suggestion-kind">{suggestion.kind === 'skill' ? 'Skill confirmation' : 'Review prompt'}</span>
              <b>{suggestion.skill || suggestion.display}</b>
              <span>{suggestion.kind === 'skill' ? `I confirm I have ${suggestion.skill}; add it to my Skills section.` : suggestion.text}</span>
            </span>
          </label>
        )) : <p className="empty-note">Nothing to add. Your skills align with the role.</p>}
      </div>
      {hiddenCount > 0 && (
        <button className="suggestion-toggle" type="button" onClick={() => setExpanded((value) => !value)}>
          <ChevronDown className={expanded ? 'is-open' : ''} size={15} />
          {expanded ? 'Show fewer suggestions' : `Show ${hiddenCount} more suggestion${hiddenCount === 1 ? '' : 's'}`}
        </button>
      )}
      {error && <p className="error-banner" role="alert">{error}</p>}
      <button
        className="button-secondary suggestion-action"
        type="button"
        onClick={onReview}
        disabled={disabled || updating || selected.length === 0}
      >
        {updating
          ? <><LoaderCircle className="spin" size={15} /> Updating…</>
          : <>Add selected skills &amp; review resume <ArrowRight size={16} /></>}
      </button>
      {disabled && <p className="panel-footnote">Open a live analysis to apply suggestions. Saved analyses are read-only.</p>}
    </section>
  )
}
