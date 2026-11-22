import React, { useMemo, useState } from 'react'
import { Check, Copy, FilePlus2, LayoutTemplate, Plus, Trash2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useWorkspace } from '../context/WorkspaceContext.jsx'
import {
  RESUME_TEMPLATES,
  buildResumeSections,
  buildResumeText,
  createBuilderState,
  getResumeTemplate,
} from '../data/resumeTemplates.js'

function patchExperience(form, id, patch) {
  return {
    ...form,
    experience: form.experience.map((entry) => (entry.id === id ? { ...entry, ...patch } : entry)),
  }
}

function patchEducation(form, id, patch) {
  return {
    ...form,
    education: form.education.map((entry) => (entry.id === id ? { ...entry, ...patch } : entry)),
  }
}

function addExperience(form) {
  const nextId = Math.max(0, ...form.experience.map((entry) => entry.id)) + 1
  return {
    ...form,
    experience: [...form.experience, { id: nextId, role: '', company: '', startDate: '', endDate: '', points: [''] }],
  }
}

function removeExperience(form, id) {
  return { ...form, experience: form.experience.filter((entry) => entry.id !== id) }
}

function addEducation(form) {
  const nextId = Math.max(0, ...form.education.map((entry) => entry.id)) + 1
  return { ...form, education: [...form.education, { id: nextId, school: '', degree: '', year: '' }] }
}

function removeEducation(form, id) {
  return { ...form, education: form.education.filter((entry) => entry.id !== id) }
}

function renderBlocks(sections) {
  const blocks = []
  for (const section of sections) {
    if (section.heading) blocks.push({ type: 'heading', text: section.heading })
    for (const line of section.lines) {
      const text = String(line)
      if (text.startsWith('- ')) blocks.push({ type: 'bullet', text: text.slice(2).trim() })
      else blocks.push({ type: 'line', text })
    }
  }
  return blocks
}

export default function ResumeBuilder() {
  const navigate = useNavigate()
  const { setResumeText } = useWorkspace()
  const [templateId, setTemplateId] = useState(RESUME_TEMPLATES[0].id)
  const [form, setForm] = useState(createBuilderState)
  const [copied, setCopied] = useState(false)

  const template = getResumeTemplate(templateId)
  const sections = useMemo(() => buildResumeSections(form, template), [form, template])
  const resumeText = useMemo(() => buildResumeText(form, template), [form, template])
  const blocks = useMemo(() => renderBlocks(sections), [sections])

  function update(patch) {
    setForm((current) => ({ ...current, ...patch }))
  }

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(resumeText)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 2000)
    } catch {
      setCopied(false)
    }
  }

  function handleUseInAnalysis() {
    setResumeText(resumeText)
    navigate('/analyze', { state: { fromBuilder: true } })
  }

  function fieldId(key) {
    return `builder-${key}`
  }

  return (
    <div className="rb">
      <div className="rb-templates" role="radiogroup" aria-label="ATS-friendly resume templates">
        {RESUME_TEMPLATES.map((candidate) => (
          <button
            key={candidate.id}
            type="button"
            role="radio"
            aria-checked={candidate.id === templateId}
            className={`rb-template-card ${candidate.id === templateId ? 'is-selected' : ''}`}
            onClick={() => setTemplateId(candidate.id)}
          >
            <span className="rb-template-icon">
              <LayoutTemplate size={18} />
            </span>
            <span className="rb-template-name">{candidate.name}</span>
            <span className="rb-template-tagline">{candidate.tagline}</span>
            {candidate.recommended ? <span className="rb-template-badge">Recommended</span> : null}
          </button>
        ))}
      </div>

      <div className="rb-grid">
        <div className="rb-form">
          <div className="rb-form-section">
            <span className="rb-form-kicker">Your details</span>
            <div className="rb-grid-2">
              <label className="rb-field" htmlFor={fieldId('name')}>
                <span>Full name</span>
                <input
                  id={fieldId('name')}
                  className="rb-input"
                  type="text"
                  value={form.name}
                  onChange={(event) => update({ name: event.target.value })}
                  placeholder="e.g. Avery Chen"
                />
              </label>
              <label className="rb-field" htmlFor={fieldId('title')}>
                <span>Target or current job title</span>
                <input
                  id={fieldId('title')}
                  className="rb-input"
                  type="text"
                  value={form.title}
                  onChange={(event) => update({ title: event.target.value })}
                  placeholder="e.g. Senior Data Analyst"
                />
              </label>
            </div>
          </div>

          {(template.sections || []).map((section) => {
            if (section.id === 'summary') {
              return (
                <div className="rb-form-section" key={section.id}>
                  <span className="rb-form-kicker">{section.label.toUpperCase()}</span>
                  <label className="rb-field" htmlFor={fieldId('summary')}>
                    <span>Professional summary</span>
                    <textarea
                      id={fieldId('summary')}
                      className="rb-input rb-textarea"
                      rows={3}
                      value={form.summary}
                      onChange={(event) => update({ summary: event.target.value })}
                      placeholder="Two or three honest sentences about your background."
                    />
                  </label>
                </div>
              )
            }

            if (section.id === 'skills') {
              return (
                <div className="rb-form-section" key={section.id}>
                  <span className="rb-form-kicker">{section.label.toUpperCase()}</span>
                  <label className="rb-field" htmlFor={fieldId('skills')}>
                    <span>Skills</span>
                    <input
                      id={fieldId('skills')}
                      className="rb-input"
                      type="text"
                      value={form.skills}
                      onChange={(event) => update({ skills: event.target.value })}
                      placeholder="e.g. SQL, Python, data modeling"
                    />
                  </label>
                  <p className="rb-hint">Separate multiple skills with commas.</p>
                </div>
              )
            }

            if (section.id === 'experience') {
              return (
                <div className="rb-form-section" key={section.id}>
                  <span className="rb-form-kicker">{section.label.toUpperCase()}</span>
                  <div className="rb-experience-list">
                    {form.experience.map((entry) => (
                      <div className="rb-experience" key={entry.id}>
                        <div className="rb-grid-2">
                          <label className="rb-field" htmlFor={`builder-exp-${entry.id}-role`}>
                            <span>Role</span>
                            <input
                              id={`builder-exp-${entry.id}-role`}
                              className="rb-input"
                              type="text"
                              value={entry.role}
                              onChange={(event) => update(patchExperience(form, entry.id, { role: event.target.value }))}
                              placeholder="e.g. Senior Data Analyst"
                            />
                          </label>
                          <label className="rb-field" htmlFor={`builder-exp-${entry.id}-company`}>
                            <span>Company</span>
                            <input
                              id={`builder-exp-${entry.id}-company`}
                              className="rb-input"
                              type="text"
                              value={entry.company}
                              onChange={(event) => update(patchExperience(form, entry.id, { company: event.target.value }))}
                              placeholder="e.g. Northwind Retail"
                            />
                          </label>
                        </div>
                        <div className="rb-grid-3">
                          <label className="rb-field" htmlFor={`builder-exp-${entry.id}-start`}>
                            <span>Start</span>
                            <input
                              id={`builder-exp-${entry.id}-start`}
                              className="rb-input"
                              type="text"
                              value={entry.startDate}
                              onChange={(event) => update(patchExperience(form, entry.id, { startDate: event.target.value }))}
                              placeholder="e.g. 2021"
                            />
                          </label>
                          <label className="rb-field" htmlFor={`builder-exp-${entry.id}-end`}>
                            <span>End</span>
                            <input
                              id={`builder-exp-${entry.id}-end`}
                              className="rb-input"
                              type="text"
                              value={entry.endDate}
                              onChange={(event) => update(patchExperience(form, entry.id, { endDate: event.target.value }))}
                              placeholder="e.g. 2024"
                            />
                          </label>
                        </div>
                        <label className="rb-field" htmlFor={`builder-exp-${entry.id}-points`}>
                          <span>Key responsibilities or wins</span>
                          <textarea
                            id={`builder-exp-${entry.id}-points`}
                            className="rb-input rb-textarea"
                            rows={3}
                            value={entry.points.join('\n')}
                            onChange={(event) => update(patchExperience(form, entry.id, { points: event.target.value.split(/\r?\n/) }))}
                            placeholder="One responsibility or achievement per line."
                          />
                        </label>
                        <div className="rb-row-actions">
                          <button className="rb-button rb-button-ghost" type="button" onClick={() => update(addExperience(form))}>
                            <Plus size={15} /> Add role
                          </button>
                          <button className="rb-button rb-button-ghost" type="button" onClick={() => update(removeExperience(form, entry.id))} disabled={form.experience.length <= 1}>
                            <Trash2 size={15} /> Remove
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )
            }

            if (section.id === 'education') {
              return (
                <div className="rb-form-section" key={section.id}>
                  <span className="rb-form-kicker">{section.label.toUpperCase()}</span>
                  <div className="rb-experience-list">
                    {form.education.map((entry) => (
                      <div className="rb-experience" key={entry.id}>
                        <div className="rb-grid-3">
                          <label className="rb-field" htmlFor={`builder-edu-${entry.id}-school`}>
                            <span>School</span>
                            <input
                              id={`builder-edu-${entry.id}-school`}
                              className="rb-input"
                              type="text"
                              value={entry.school}
                              onChange={(event) => update(patchEducation(form, entry.id, { school: event.target.value }))}
                              placeholder="e.g. State University"
                            />
                          </label>
                          <label className="rb-field" htmlFor={`builder-edu-${entry.id}-degree`}>
                            <span>Degree</span>
                            <input
                              id={`builder-edu-${entry.id}-degree`}
                              className="rb-input"
                              type="text"
                              value={entry.degree}
                              onChange={(event) => update(patchEducation(form, entry.id, { degree: event.target.value }))}
                              placeholder="e.g. BSc Economics"
                            />
                          </label>
                          <label className="rb-field" htmlFor={`builder-edu-${entry.id}-year`}>
                            <span>Year</span>
                            <input
                              id={`builder-edu-${entry.id}-year`}
                              className="rb-input"
                              type="text"
                              value={entry.year}
                              onChange={(event) => update(patchEducation(form, entry.id, { year: event.target.value }))}
                              placeholder="e.g. 2018"
                            />
                          </label>
                        </div>
                        <div className="rb-row-actions">
                          <button className="rb-button rb-button-ghost" type="button" onClick={() => update(addEducation(form))}>
                            <Plus size={15} /> Add education
                          </button>
                          <button
                            className="rb-button rb-button-ghost"
                            type="button"
                            onClick={() => update(removeEducation(form, entry.id))}
                            disabled={form.education.length <= 1}
                          >
                            <Trash2 size={15} /> Remove
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )
            }

            if (section.id === 'certifications') {
              return (
                <div className="rb-form-section" key={section.id}>
                  <span className="rb-form-kicker">{section.label.toUpperCase()}</span>
                  <label className="rb-field" htmlFor={fieldId('certifications')}>
                    <span>Certifications</span>
                    <input
                      id={fieldId('certifications')}
                      className="rb-input"
                      type="text"
                      value={form.certifications}
                      onChange={(event) => update({ certifications: event.target.value })}
                      placeholder="e.g. AWS Solutions Architect"
                    />
                  </label>
                  <p className="rb-hint">Separate multiple certifications with commas.</p>
                </div>
              )
            }

            return null
          })}

          <div className="rb-actions">
            <button className="button-primary" type="button" onClick={handleUseInAnalysis}>
              <FilePlus2 size={16} /> Use in analysis
            </button>
            <button className="button-secondary" type="button" onClick={handleCopy}>
              {copied ? <Check size={16} /> : <Copy size={16} />}
              {copied ? 'Copied' : 'Copy text'}
            </button>
            <button className="rb-button rb-button-ghost" type="button" onClick={() => setForm(createBuilderState())}>
              <Plus size={15} /> Reset
            </button>
          </div>
          <p className="rb-note">
            The builder only uses the details you enter. Nothing is invented, and the ATS score you get later is an estimate.
          </p>
        </div>

        <div className="rb-preview-panel">
          <div className="panel-heading">
            <div>
              <span className="panel-kicker">Live preview</span>
              <h2>{template.name}</h2>
            </div>
          </div>
          <div className="rb-preview">
            {blocks.map((block, index) => {
              if (block.type === 'heading') return <p key={index} className="rb-preview-heading">{block.text}</p>
              if (block.type === 'bullet') return <p key={index} className="rb-preview-line is-bullet">- {block.text}</p>
              return <p key={index} className="rb-preview-line">{block.text}</p>
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
