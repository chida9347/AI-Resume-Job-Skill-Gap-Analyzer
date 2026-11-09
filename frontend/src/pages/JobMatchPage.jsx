import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertCircle,
  ArrowLeft,
  BriefcaseBusiness,
  CircleHelp,
  LoaderCircle,
  Plus,
  Sparkles,
  Trash2,
  Trophy,
} from 'lucide-react'
import { JobComponentsChart } from '../components/charts/ResultsCharts.jsx'
import ErrorBanner from '../components/ui/ErrorBanner.jsx'
import { useWorkspace } from '../context/WorkspaceContext.jsx'
import * as api from '../services/api.js'
import { getErrorMessage } from '../utils/errors.js'

function blankJob() {
  return { id: crypto.randomUUID(), title: '', company: '', text: '' }
}

const MAX_JOBS = 25

export default function JobMatchPage() {
  const { resumeText: workspaceResume } = useWorkspace()
  const [resumeText, setResumeText] = useState(workspaceResume || '')
  const [jobs, setJobs] = useState([blankJob(), blankJob()])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  function updateJob(id, changes) {
    setJobs((current) => current.map((job) => (job.id === id ? { ...job, ...changes } : job)))
  }

  function addJob() {
    if (jobs.length >= MAX_JOBS) return
    setJobs((current) => [...current, blankJob()])
  }

  function removeJob(id) {
    setJobs((current) => (current.length === 1 ? current : current.filter((job) => job.id !== id)))
  }

  async function submit(event) {
    event.preventDefault()
    setError('')
    if (resumeText.trim().length < 40) {
      setError('Add a little more resume text so the comparison has enough to work with.')
      return
    }
    const usable = jobs.filter((job) => job.text.trim().length >= 40)
    if (!usable.length) {
      setError('Add at least one job description with a few sentences.')
      return
    }
    setLoading(true)
    try {
      const data = await api.rankJobs(resumeText, usable)
      setResult(data)
    } catch (failure) {
      setError(getErrorMessage(failure, 'The roles could not be compared. Check the API connection and try again.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="jobmatch-page">
      <div className="page-heading">
        <div className="eyebrow"><span className="eyebrow-line" /> ONE RESUME, SEVERAL ROLES</div>
        <h1>Compare <span>roles.</span></h1>
        <p>
          Rank up to {MAX_JOBS} postings against one resume. Every score is a weighted estimate with the components
          shown, not an employer ATS result.
        </p>
      </div>

      {workspaceResume && (
        <div className="editor-note" role="status">
          <Sparkles size={17} />
          <div>
            <b>Using your current resume draft</b>
            <span>You can edit the text below without changing your analysis workspace.</span>
          </div>
        </div>
      )}

      <form className="jobmatch-form" onSubmit={submit}>
        <section className="jobmatch-resume">
          <div className="panel-heading">
            <div><span className="panel-kicker">01 / RESUME</span><h2>Resume text</h2></div>
            <span className="count-pill">{resumeText.trim() ? resumeText.trim().split(/\s+/).length : 0} words</span>
          </div>
          <textarea
            className="job-textarea"
            value={resumeText}
            onChange={(event) => setResumeText(event.target.value)}
            rows={10}
            maxLength={100000}
            aria-label="Resume text for job comparison"
            placeholder="Paste the resume text you want to compare with each role."
          />
        </section>

        <section className="jobmatch-jobs">
          <div className="panel-heading">
            <div><span className="panel-kicker">02 / ROLES</span><h2>Job postings</h2></div>
            <button className="button-secondary" type="button" onClick={addJob} disabled={jobs.length >= MAX_JOBS}>
              <Plus size={15} /> Add role
            </button>
          </div>
          {jobs.map((job, index) => (
            <article className="jobmatch-card" key={job.id}>
              <div className="jobmatch-card-head">
                <span className="learning-number">{String(index + 1).padStart(2, '0')}</span>
                <div className="jobmatch-fields">
                  <label>
                    <span>Role title <small>OPTIONAL</small></span>
                    <input value={job.title} onChange={(event) => updateJob(job.id, { title: event.target.value })} placeholder="e.g. Backend Engineer" />
                  </label>
                  <label>
                    <span>Company <small>OPTIONAL</small></span>
                    <input value={job.company} onChange={(event) => updateJob(job.id, { company: event.target.value })} placeholder="e.g. Acme" />
                  </label>
                </div>
                <button className="icon-link danger-link" type="button" onClick={() => removeJob(job.id)} aria-label="Remove role" title="Remove role">
                  <Trash2 size={16} />
                </button>
              </div>
              <textarea
                className="job-textarea"
                value={job.text}
                onChange={(event) => updateJob(job.id, { text: event.target.value })}
                rows={5}
                maxLength={100000}
                aria-label={`Job description ${index + 1}`}
                placeholder="Paste the full job description here."
              />
            </article>
          ))}
        </section>

        {error && <ErrorBanner>{error}</ErrorBanner>}

        <div className="form-footer">
          <span className="editor-hint">Roles with no text are ignored. You can compare up to {MAX_JOBS} at once.</span>
          <button className="button-primary" type="submit" disabled={loading}>
            {loading ? <LoaderCircle className="spin" size={16} /> : <BriefcaseBusiness size={16} />}
            {loading ? 'Comparing roles…' : 'Rank these roles'}
          </button>
        </div>
      </form>

      {result && (
        <section className="jobmatch-results">
          <div className="results-heading">
            <div>
              <div className="eyebrow"><span className="eyebrow-line" /> RANKED RESULT</div>
              <h1>Best <span>match.</span></h1>
              <p>{result.disclaimer}</p>
            </div>
          </div>

          {result.best_match && (
            <article className="best-match-card">
              <div className="best-match-copy">
                <span className="panel-kicker"><Trophy size={14} /> TOP RANKED ROLE</span>
                <h2>{result.best_match.title}</h2>
                {result.best_match.company && <p>{result.best_match.company}</p>}
                <p className="best-match-explanation">{result.best_match.explanation}</p>
                <div className="best-match-stats">
                  <div><b>{result.best_match.compatibility_score}</b><span>compatibility</span></div>
                  <div><b>{result.best_match.required_coverage}%</b><span>required coverage</span></div>
                  <div><b>{result.best_match.ats_score}</b><span>ATS estimate</span></div>
                </div>
                {result.best_match.top_gaps?.length > 0 && (
                  <div className="best-match-gaps">
                    <b>Largest gaps</b>
                    <div className="feature-tags">
                      {result.best_match.top_gaps.map((gap) => <span className="feature-tag feature-tag-missing" key={gap}>{gap}</span>)}
                    </div>
                  </div>
                )}
              </div>
              <div className="best-match-chart">
                <JobComponentsChart components={result.best_match.components} labels={result.component_labels} />
              </div>
            </article>
          )}

          <div className="job-ranking-list">
            {result.jobs.map((job) => (
              <article className="job-ranking-row" key={`${job.id}-${job.rank}`}>
                <span className="ranking-number">#{job.rank}</span>
                <div className="ranking-copy">
                  <b>{job.title}</b>
                  <small>{job.company || 'Company not supplied'} · {job.explanation}</small>
                  {job.top_gaps?.length > 0 && (
                    <div className="feature-tags">
                      {job.top_gaps.slice(0, 4).map((gap) => <span className="feature-tag feature-tag-missing" key={gap}>{gap}</span>)}
                    </div>
                  )}
                </div>
                <div className="ranking-score">
                  <b>{job.compatibility_score}</b><span>/100</span>
                </div>
              </article>
            ))}
          </div>

          {result.ranking_explanations?.length > 0 && (
            <section className="ranking-explanations">
              <div className="panel-heading">
                <div><span className="panel-kicker">WHY THE ORDER</span><h2>Ranking notes</h2></div>
                <CircleHelp size={19} />
              </div>
              {result.ranking_explanations.map((note) => (
                <p key={`${note.higher}-${note.lower}`}><AlertCircle size={14} /> {note.summary}</p>
              ))}
            </section>
          )}

          <div className="results-bottom">
            <span>Weights: {Object.entries(result.weights).map(([key, value]) => `${result.component_labels[key] || key} ${Math.round(value * 100)}%`).join(' · ')}</span>
            <Link className="text-button" to="/results"><ArrowLeft size={15} /> Back to your analysis</Link>
          </div>
        </section>
      )}
    </section>
  )
}
