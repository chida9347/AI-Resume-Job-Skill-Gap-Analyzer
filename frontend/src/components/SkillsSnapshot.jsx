import React from 'react'
import { CircleHelp, Target } from 'lucide-react'

function labelFor(comparison, skill) {
  return comparison?.skill_labels?.[skill] || skill
}

export default function SkillsSnapshot({ comparison }) {
  const matched = comparison?.matched_skills || comparison?.matched_required || []
  const missing = comparison?.missing_skills || comparison?.missing_required || []
  const partial = comparison?.partial_required || []
  const matchedPreferred = comparison?.matched_preferred || comparison?.matched_preferred_skills || []
  const missingPreferred = comparison?.missing_preferred || comparison?.missing_preferred_skills || []
  const preferredTotal = matchedPreferred.length + missingPreferred.length
  const evidence = comparison?.evidence || {}

  return (
    <section className="result-panel skills-panel">
      <div className="panel-heading">
        <div><span className="panel-kicker">01 / SKILLS</span><h2>Skills snapshot</h2></div>
        <Target size={19} />
      </div>

      <div className="skill-group">
        <h3>
          <span className="status-dot dot-green" /> Found in both
          <span className="count-pill">{matched.length}</span>
        </h3>
        <div className="skill-list">
          {matched.length ? matched.map((skill) => {
            const snippet = evidence[skill]?.[0]?.sentence
            return (
              <span className="skill-tag tag-match" key={skill} title={snippet || undefined}>
                {labelFor(comparison, skill)}
              </span>
            )
          }) : <p className="empty-note">No requested skills were found in the resume text.</p>}
        </div>
      </div>

      {partial.length > 0 && (
        <>
          <div className="panel-divider" />
          <div className="skill-group">
            <h3>
              <span className="status-dot dot-amber" /> Related, not explicit
              <span className="count-pill">{partial.length}</span>
            </h3>
            <div className="skill-list">
              {partial.map((skill) => (
                <span className="skill-tag tag-partial" key={skill} title="A related skill was found. This does not count as proven experience.">
                  {labelFor(comparison, skill)}
                </span>
              ))}
            </div>
            <p className="empty-note">A related skill was detected. It is not counted as an explicit match.</p>
          </div>
        </>
      )}

      <div className="panel-divider" />
      <div className="skill-group">
        <h3>
          <span className="status-dot dot-coral" /> Not found in resume
          <span className="count-pill">{missing.length}</span>
        </h3>
        <div className="skill-list">
          {missing.length ? missing.map((skill) => (
            <span className="skill-tag tag-missing" key={skill}>{labelFor(comparison, skill)}</span>
          )) : <p className="empty-note">All detected job skills appear in the resume text.</p>}
        </div>
      </div>

      {preferredTotal > 0 && (
        <>
          <div className="panel-divider" />
          <div className="skill-group">
            <h3>
              <span className="status-dot dot-green" /> Preferred skills
              <span className="count-pill">{matchedPreferred.length}/{preferredTotal}</span>
            </h3>
            <div className="skill-list">
              {matchedPreferred.map((skill) => (
                <span className="skill-tag tag-match" key={`matched-${skill}`}>{labelFor(comparison, skill)}</span>
              ))}
              {missingPreferred.map((skill) => (
                <span className="skill-tag" key={`missing-${skill}`}>{labelFor(comparison, skill)}</span>
              ))}
            </div>
          </div>
        </>
      )}

      <div className="panel-footnote">
        <CircleHelp size={14} /> This checks resume wording; it cannot tell whether you have an unlisted skill.
      </div>
    </section>
  )
}
