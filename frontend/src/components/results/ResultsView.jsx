import React, { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  ArrowRight,
  BarChart3,
  BriefcaseBusiness,
  CircleHelp,
  FileText,
  LoaderCircle,
  PencilLine,
  Sparkles,
  Target,
} from 'lucide-react'
import ATSPanel from '../ATSPanel.jsx'
import InterviewPreview from '../InterviewPreview.jsx'
import LearningPaths from '../LearningPaths.jsx'
import ResumeRewrite from '../ResumeRewrite.jsx'
import SkillsSnapshot from '../SkillsSnapshot.jsx'
import SuggestionsPanel from '../SuggestionsPanel.jsx'
import { CoverageChart } from '../charts/ResultsCharts.jsx'
import { useWorkspace } from '../../context/WorkspaceContext.jsx'
import { analysisCounts, atsFeedbackAsSuggestions, interviewFromAnalysis } from '../../utils/analysis.js'
import { getErrorMessage } from '../../utils/errors.js'
import { downloadTextAsPdf } from '../../utils/pdf.js'

function JobSummary({ job }) {
  if (!job || (!job.title && !job.company && !job.required_skills?.length)) return null
  const required = job.required_skills || []
  const preferred = job.preferred_skills || []
  return (
    <section className="result-panel job-summary-panel">
      <div className="panel-heading">
        <div><span className="panel-kicker">04 / TARGET ROLE</span><h2>{job.title || 'Target role'}</h2></div>
        <BriefcaseBusiness size={19} />
      </div>
      {job.company && <p className="job-company">{job.company}</p>}
      <div className="job-summary-stats">
        <div><b>{required.length}</b><span>required skills</span></div>
        <div><b>{preferred.length}</b><span>preferred skills</span></div>
        <div><b>{job.experience?.min_years ?? '—'}</b><span>years requested</span></div>
      </div>
      {job.education?.required && <p className="job-detail"><b>Education:</b> a degree or diploma is requested.</p>}
      {job.warnings?.length > 0 && (
        <div className="job-warning"><CircleHelp size={14} /><span>{job.warnings[0]}</span></div>
      )}
    </section>
  )
}

export default function ResultsView({ analysis, saved = false, savedAt = '' }) {
  const navigate = useNavigate()
  const { applySuggestions, applyRewrite, resumeText, role, fitToOnePage } = useWorkspace()
  const [selected, setSelected] = useState([])
  const [applying, setApplying] = useState(false)
  const [actionError, setActionError] = useState('')

  const comparison = analysis?.comparison || {}
  const ats = analysis?.ats || null
  const interview = useMemo(() => interviewFromAnalysis(analysis), [analysis])
  const learningPaths = analysis?.learning_paths || []
  const counts = analysisCounts(analysis)
  const suggestions = useMemo(
    () => [...(analysis?.suggestions || []), ...atsFeedbackAsSuggestions(ats)],
    [analysis, ats],
  )
  const rewrite = analysis?.rewrite || null
  const resumeConfidence =
    analysis?.meta?.resume_confidence ??
    analysis?.structured_resume?.confidence ??
    comparison?.confidence ??
    null
  const wordCount = analysis?.meta?.resume_word_count ?? analysis?.structured_resume?.word_count ?? null
  const detectedSections = Object.entries(analysis?.structured_resume?.section_presence || {})
    .filter(([, present]) => present)
    .map(([key]) => key)

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
      <div className="results-heading">
        <div>
          <div className="eyebrow"><span className="eyebrow-line" /> {saved ? 'SAVED ANALYSIS' : 'YOUR RESULTS'}</div>
          <h1>{saved ? <>Saved <span>analysis.</span></> : <>Resume <span>analysis.</span></>}</h1>
          <p>
            {counts.matched} of {counts.total} requested skills are evidenced in the resume text.
            {counts.partial > 0 ? ` ${counts.partial} related skill${counts.partial === 1 ? '' : 's'} are shown separately and do not count as proven experience.` : ''}
            {savedAt ? ` Saved ${savedAt}.` : ''}
          </p>
        </div>
        <div className="results-metrics">
          <div className="score-block">
            <div className="score-value">{counts.skillMatch}<span>%</span></div>
            <div className="score-label">SKILL MATCH</div>
            <div className="score-track"><i style={{ width: `${counts.skillMatch}%` }} /></div>
          </div>
          <div className="score-block ats-top-score">
            <div className="score-value">{ats ? ats.ats_score : '--'}<span>{ats ? '/100' : ''}</span></div>
            <div className="score-label">ATS ESTIMATE</div>
            <div className="score-hint">Keywords + sections + format</div>
          </div>
        </div>
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

      <div className="results-grid grid">
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

      <div className="results-visuals">
        <section className="result-panel chart-panel">
          <div className="panel-heading">
            <div><span className="panel-kicker">03 / COVERAGE</span><h2>Coverage at a glance</h2></div>
            <BarChart3 size={19} />
          </div>
          <CoverageChart comparison={comparison} ats={ats} />
        </section>
        <JobSummary job={analysis?.job} />
        {!analysis?.job?.title && (
          <section className="result-panel chart-panel">
            <div className="panel-heading">
              <div><span className="panel-kicker">04 / WHAT THIS MEANS</span><h2>How to read this report</h2></div>
              <Target size={19} />
            </div>
            <div className="reading-guide">
              <p><b>Skill match</b> counts required skills explicitly evidenced in your resume text.</p>
              <p><b>Partial matches</b> are related skills, never proof that you used the required skill.</p>
              <p><b>ATS estimate</b> is an explainable estimate capped below a perfect score when evidence is missing.</p>
            </div>
          </section>
        )}
      </div>

      <details className="more-insights" open>
        <summary>Detailed analysis, rewrite and interview prep</summary>
        <div className="advanced-features grid" aria-label="More analysis">
          <ATSPanel result={ats} loading={false} error={saved && !ats?.ats_score ? 'No ATS detail was stored with this analysis.' : ''} />
          {rewrite && (
            <ResumeRewrite
              result={rewrite}
              loading={false}
              error={analysis?.rewriteError || ''}
              onApply={handleApplyRewrite}
              onDownload={handleDownloadRewrite}
              applying={false}
            />
          )}
          {analysis?.rewriteError && (
            <section className="advanced-card rewrite-card">
              <div className="advanced-card-heading">
                <div><span className="panel-kicker">06 / ROLE ALIGNMENT</span><h2>Resume Rewrite</h2></div>
                <Sparkles size={19} />
              </div>
              <div className="feature-error" role="alert"><CircleHelp size={15} /> {analysis.rewriteError}</div>
            </section>
          )}
          <LearningPaths
            paths={learningPaths}
            loading={false}
            error=""
            hasGaps={(comparison.missing_required || comparison.missing_skills || []).length > 0 || (comparison.partial_required || []).length > 0}
          />
        </div>
        {interview.questions.length > 0 ? (
          <InterviewPreview
            tips={{ role: interview.role, questions: interview.questions.map((item) => ({ ...item, example_answer: item.framework })), tips: interview.tips }}
            loading={false}
            error=""
            onOpen={() => navigate('/interview')}
          />
        ) : (
          <section className="interview-preview">
            <div className="interview-preview-heading">
              <div><span className="panel-kicker">04 / PREPARE</span><h2>Interview questions</h2><p>Saved analyses do not include the generated question set.</p></div>
              <Link className="button-secondary" to="/analyze">Run a new analysis <ArrowRight size={15} /></Link>
            </div>
          </section>
        )}
      </details>

      <div className="results-actions">
        {!saved && resumeText && (
          <button className="button-primary" type="button" onClick={() => navigate('/editor')}>
            <PencilLine size={16} /> Edit resume
          </button>
        )}
        <button className="button-secondary" type="button" onClick={() => navigate('/roadmap')}>
          <Target size={16} /> Learning roadmap
        </button>
        <button className="button-secondary" type="button" onClick={() => navigate('/interview')}>
          <Sparkles size={16} /> Mock interview
        </button>
        <button className="button-secondary" type="button" onClick={() => navigate('/jobs')}>
          <BriefcaseBusiness size={16} /> Compare jobs
        </button>
        {applying && <span className="inline-status"><LoaderCircle className="spin" size={15} /> Updating resume…</span>}
      </div>

      <div className="results-bottom">
        <span>Made from your resume and this job description. Scores are estimates, not employer ATS results.</span>
        <Link className="text-button" to="/analyze"><ArrowLeft size={15} /> Edit inputs</Link>
      </div>
    </section>
  )
}
