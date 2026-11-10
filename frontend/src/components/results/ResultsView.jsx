import React, { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  ArrowRight,
  BriefcaseBusiness,
  CircleHelp,
  FileText,
  PencilLine,
  Target,
} from 'lucide-react'
import ATSPanel from '../ATSPanel.jsx'
import InterviewPreview from '../InterviewPreview.jsx'
import LearningPaths from '../LearningPaths.jsx'
import ResumeRewrite from '../ResumeRewrite.jsx'
import SkillsSnapshot from '../SkillsSnapshot.jsx'
import SuggestionsPanel from '../SuggestionsPanel.jsx'
import { useWorkspace } from '../../context/WorkspaceContext.jsx'
import { analysisCounts, interviewFromAnalysis } from '../../utils/analysis.js'
import { getErrorMessage } from '../../utils/errors.js'
import { downloadTextAsPdf } from '../../utils/pdf.js'

export default function ResultsView({ analysis, saved = false, savedAt = '' }) {
  const navigate = useNavigate()
  const { applySuggestions, applyRewrite, resumeText, role } = useWorkspace()
  const [selected, setSelected] = useState([])
  const [applying, setApplying] = useState(false)
  const [actionError, setActionError] = useState('')

  const comparison = analysis?.comparison || {}
  const ats = analysis?.ats || null
  const job = analysis?.job || {}
  const interview = useMemo(() => interviewFromAnalysis(analysis), [analysis])
  const learningPaths = analysis?.learning_paths || []
  const counts = analysisCounts(analysis)
  const suggestions = useMemo(() => analysis?.suggestions || [], [analysis])
  const rewrite = analysis?.rewrite || null
  const atsScore = Number.isFinite(Number(ats?.ats_score)) ? Number(ats.ats_score) : null
  const requiredTotal = counts.total
  const preferredTotal = (job.preferred_skills || []).length
  const roleTitle = job.title || analysis?.interview?.role || role || 'Target role'
  const hasGaps = counts.missing > 0 || counts.partial > 0
  const resumeConfidence =
    analysis?.meta?.resume_confidence ??
    analysis?.structured_resume?.confidence ??
    comparison?.confidence ??
    null
  const wordCount = analysis?.meta?.resume_word_count ?? analysis?.structured_resume?.word_count ?? null
  const detectedSections = Object.entries(analysis?.structured_resume?.section_presence || {})
    .filter(([, present]) => present)
    .map(([key]) => key)

  const summaryParts = []
  if (requiredTotal > 0) {
    summaryParts.push(`${counts.matched} of ${requiredTotal} required skills are explicitly evidenced in the resume text.`)
  } else {
    summaryParts.push('The resume text was compared with the job description.')
  }
  if (counts.partial > 0) {
    summaryParts.push(
      `${counts.partial} related skill${counts.partial === 1 ? ' is' : 's are'} shown separately and do not count as proven experience.`,
    )
  }
  if (savedAt) summaryParts.push(`Saved ${savedAt}.`)

  function toggleSuggestion(id) {
    setSelected((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]))
  }

  async function handleApply() {
    const selectedItems = suggestions.filter((item) => selected.includes(item.id))
    if (!selectedItems.length) return
    setApplying(true)
    setActionError('')
    try {
      await applySuggestions(selectedItems)
      navigate('/editor')
    } catch (error) {
      setActionError(getErrorMessage(error, 'The resume could not be updated. Check the API connection and try again.'))
    } finally {
      setApplying(false)
    }
  }

  function handleApplyRewrite() {
    if (!rewrite?.rewritten) return
    applyRewrite(rewrite.rewritten)
    navigate('/editor')
  }

  function handleDownloadRewrite() {
    if (!rewrite?.rewritten) return
    downloadTextAsPdf({
      text: rewrite.rewritten,
      filename: 'rewritten-resume.pdf',
      targetRole: role,
      fitToOnePage: false,
      onError: setActionError,
    })
  }

  return (
    <section className="results-page">
      <header className="results-heading">
        <div className="results-heading-copy">
          <div className="eyebrow"><span className="eyebrow-line" /> {saved ? 'SAVED ANALYSIS' : 'YOUR RESULTS'}</div>
          <h1>{saved ? <>Saved <span>analysis.</span></> : <>Resume <span>analysis.</span></>}</h1>
          <p className="results-summary">{summaryParts.join(' ')}</p>
          {(job.title || job.company || requiredTotal > 0) && (
            <div className="results-role">
              <BriefcaseBusiness size={15} />
              <span><b>{roleTitle}</b>{job.company ? ` · ${job.company}` : ''}</span>
              {requiredTotal > 0 && (
                <span className="results-role-meta">
                  {requiredTotal} required{preferredTotal > 0 ? ` · ${preferredTotal} preferred` : ''}
                </span>
              )}
            </div>
          )}
          {job.warnings?.length > 0 && (
            <p className="results-role-warning"><CircleHelp size={14} /><span>{job.warnings[0]}</span></p>
          )}
        </div>
        <div className="results-heading-actions">
          {!saved && resumeText && (
            <button className="button-primary" type="button" onClick={() => navigate('/editor')}>
              <PencilLine size={16} /> Edit resume
            </button>
          )}
          <button className="button-secondary" type="button" onClick={() => navigate('/roadmap')}>
            <Target size={16} /> Learning roadmap
          </button>
          <button className="button-secondary" type="button" onClick={() => navigate('/jobs')}>
            <BriefcaseBusiness size={16} /> Compare jobs
          </button>
        </div>
      </header>

      <div className="results-overview" aria-label="Analysis summary">
        <article className="overview-stat">
          <span className="overview-label">Skill match</span>
          <div className="overview-value">{counts.skillMatch}<small>%</small></div>
          <p>
            {requiredTotal > 0
              ? `${counts.matched} of ${requiredTotal} required skills evidenced`
              : 'No required skills detected in the job description'}
          </p>
          <div className="score-track" aria-hidden="true">
            <i style={{ width: `${Math.max(0, Math.min(100, counts.skillMatch))}%` }} />
          </div>
        </article>
        <article className="overview-stat">
          <span className="overview-label">ATS estimate</span>
          <div className="overview-value">
            {atsScore !== null ? atsScore : '—'}
            {atsScore !== null && <small>/100</small>}
          </div>
          <p>{atsScore !== null ? 'Keywords, sections and formatting' : 'No ATS estimate for this analysis'}</p>
        </article>
        <article className={`overview-stat ${counts.missing > 0 ? 'is-alert' : ''}`}>
          <span className="overview-label">Gaps to close</span>
          <div className="overview-value">{requiredTotal > 0 ? counts.missing : '—'}</div>
          <p>
            {requiredTotal === 0
              ? 'Run an analysis with a job description'
              : counts.partial > 0
                ? `${counts.partial} related skill${counts.partial === 1 ? '' : 's'} detected separately`
                : 'Required skills not found in the resume'}
          </p>
        </article>
      </div>

      {saved && (
        <div className="editor-note" role="status">
          <FileText size={17} />
          <div>
            <b>This is a read-only saved snapshot</b>
            <span>Resume text and the role-specific rewrite are not stored with a saved analysis. Run a new analysis to edit the resume again.</span>
          </div>
        </div>
      )}

      {resumeConfidence !== null && resumeConfidence < 75 && (
        <div className="editor-note" role="status">
          <CircleHelp size={17} />
          <div>
            <b>{resumeConfidence < 45 ? 'Limited resume text detected' : 'Resume extraction may be incomplete'}</b>
            <span>
              {wordCount ? `${wordCount} words were detected. ` : ''}
              {detectedSections.length ? `${detectedSections.length} recognizable sections were found. ` : ''}
              Check the extracted text before relying on the match results.
            </span>
          </div>
        </div>
      )}

      <div className="results-main-grid">
        <SkillsSnapshot comparison={comparison} />
        <SuggestionsPanel
          suggestions={suggestions}
          selected={selected}
          onToggle={toggleSuggestion}
          onReview={handleApply}
          updating={applying}
          error={actionError}
          disabled={saved || !resumeText}
        />
      </div>

      <ATSPanel
        result={ats}
        loading={false}
        error={saved && !ats?.ats_score ? 'No ATS detail was stored with this saved analysis.' : ''}
      />

      <div className="results-support-grid">
        <LearningPaths
          paths={learningPaths}
          loading={false}
          error=""
          hasGaps={hasGaps}
          title="Build missing skills"
        />
        {interview.questions.length > 0 ? (
          <InterviewPreview
            tips={{ role: interview.role, questions: interview.questions.map((item) => ({ ...item, example_answer: item.framework })), tips: interview.tips }}
            loading={false}
            error=""
            onOpen={() => navigate('/interview')}
          />
        ) : (
          <section className="interview-preview interview-preview-empty">
            <div className="interview-preview-heading">
              <div>
                <span className="panel-kicker">INTERVIEW PREP</span>
                <h2>Practice for this role</h2>
                <p>
                  {saved
                    ? 'Saved analyses do not include the generated question set.'
                    : 'No interview questions were generated for this analysis.'}
                </p>
              </div>
            </div>
            <Link className="button-secondary" to="/analyze">Run a new analysis <ArrowRight size={15} /></Link>
          </section>
        )}
      </div>

      {rewrite ? (
        <details className="results-rewrite">
          <summary>Optional: resume rewrite draft</summary>
          <ResumeRewrite
            result={rewrite}
            loading={false}
            error={analysis?.rewriteError || ''}
            onApply={handleApplyRewrite}
            onDownload={handleDownloadRewrite}
            applying={false}
          />
        </details>
      ) : analysis?.rewriteError ? (
        <section className="advanced-card rewrite-card">
          <div className="advanced-card-heading">
            <div><span className="panel-kicker">OPTIONAL DRAFT</span><h2>Resume rewrite</h2></div>
            <FileText size={19} />
          </div>
          <div className="feature-error" role="alert"><CircleHelp size={15} /> {analysis.rewriteError}</div>
        </section>
      ) : null}

      <details className="results-about">
        <summary>About these scores</summary>
        <div className="results-about-grid">
          <p><b>Skill match</b> counts required skills explicitly evidenced in the resume text. Related skills are shown separately and never count as proof.</p>
          <p><b>ATS estimate</b> is an explainable guide based on keywords, sections and formatting. It is not a result from an employer system.</p>
          <p><b>Learning and interview prompts</b> are practice suggestions generated from the supplied role, not guarantees or real employer questions.</p>
        </div>
      </details>

      <div className="results-bottom">
        <span>Estimates use only the resume and job text you supplied.</span>
        <Link className="text-button" to="/analyze">
          <ArrowLeft size={15} /> {saved ? 'Run a new analysis' : 'Edit inputs'}
        </Link>
      </div>
    </section>
  )
}
