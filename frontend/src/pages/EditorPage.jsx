import React, { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowDownToLine,
  ArrowLeft,
  FileText,
  LoaderCircle,
  PencilLine,
  RotateCcw,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import ResumeEditChat from '../components/ResumeEditChat.jsx'
import EmptyState from '../components/ui/EmptyState.jsx'
import ErrorBanner from '../components/ui/ErrorBanner.jsx'
import { useWorkspace } from '../context/WorkspaceContext.jsx'
import { getErrorMessage } from '../utils/errors.js'
import { downloadTextAsPdf } from '../utils/pdf.js'

export default function EditorPage() {
  const {
    analysis,
    resumeText,
    role,
    fitToOnePage,
    setResumeText,
    setFitToOnePage,
    applyChatEdit,
    appliedSkills,
    appliedReviewNotes,
    appliedRewrite,
  } = useWorkspace()
  const [error, setError] = useState('')
  const [downloading, setDownloading] = useState(false)

  const wordCount = useMemo(() => resumeText.trim().split(/\s+/).filter(Boolean).length, [resumeText])

  if (!analysis || !resumeText) {
    return (
      <EmptyState
        icon={PencilLine}
        title="No live resume to edit"
        description="Run a new analysis, or apply a suggestion or rewrite from a live result. Saved analyses are read-only snapshots and do not include resume text."
        actionLabel="Run an analysis"
        actionTo="/analyze"
      />
    )
  }

  function handleDownload() {
    setDownloading(true)
    setError('')
    try {
      const ok = downloadTextAsPdf({
        text: resumeText,
        filename: 'roleprint-resume.pdf',
        targetRole: role,
        fitToOnePage,
        onError: setError,
      })
      if (!ok && !error) setError('The PDF could not be created from this resume text.')
    } finally {
      setDownloading(false)
    }
  }

  async function handleChat(instruction) {
    const result = await applyChatEdit(instruction)
    return result
  }

  return (
    <section className="editor-page">
      <div className="page-heading editor-heading">
        <div>
          <div className="eyebrow"><span className="eyebrow-line" /> YOUR DRAFT</div>
          <h1>Edit your <span>resume.</span></h1>
          <p>Changes stay in this browser session. Download the PDF when the wording is accurate and ready.</p>
        </div>
        <div className="editor-actions">
          <Link className="button-secondary" to="/results"><ArrowLeft size={15} /> Back to results</Link>
          <button className="button-primary" type="button" onClick={handleDownload} disabled={downloading}>
            {downloading ? <LoaderCircle className="spin" size={16} /> : <ArrowDownToLine size={16} />}
            Download PDF
          </button>
        </div>
      </div>

      {(appliedSkills.length > 0 || appliedReviewNotes > 0 || appliedRewrite) && (
        <div className="editor-note" role="status">
          <Sparkles size={17} />
          <div>
            <b>Changes in this draft</b>
            <span>
              {appliedSkills.length > 0 && `${appliedSkills.length} confirmed skill${appliedSkills.length === 1 ? '' : 's'} added. `}
              {appliedReviewNotes > 0 && `${appliedReviewNotes} review note${appliedReviewNotes === 1 ? '' : 's'} added as editable text. `}
              {appliedRewrite && 'Role-alignment rewrite applied. '}
              Verify every line before downloading.
            </span>
          </div>
        </div>
      )}

      {error && <ErrorBanner>{error}</ErrorBanner>}

      <div className="editor-grid">
        <section className="editor-panel">
          <div className="panel-heading">
            <div><span className="panel-kicker">PLAIN TEXT</span><h2>Resume draft</h2></div>
            <span className="count-pill">{wordCount} words</span>
          </div>
          <textarea
            className="resume-editor"
            value={resumeText}
            onChange={(event) => setResumeText(event.target.value)}
            spellCheck
            aria-label="Resume draft text"
          />
          <div className="editor-options">
            <label className="save-history-option">
              <input
                type="checkbox"
                checked={fitToOnePage}
                onChange={(event) => setFitToOnePage(event.target.checked)}
              />
              <span><FileText size={14} /> Try to fit the PDF on one page</span>
            </label>
            <span className="editor-hint">If the text is too long to fit legibly, the download is stopped instead of shrinking it further.</span>
          </div>
          <p className="panel-footnote">
            <ShieldCheck size={14} /> PDF export formats this reviewed text. It does not reproduce the original document layout.
          </p>
        </section>

        <div className="editor-side">
          <ResumeEditChat onSend={handleChat} />
          <section className="editor-panel editor-tips">
            <div className="panel-heading">
              <div><span className="panel-kicker">ACCURACY FIRST</span><h2>Before you download</h2></div>
              <RotateCcw size={18} />
            </div>
            <ul>
              <li>Keep only skills and experience you can explain in an interview.</li>
              <li>Replace placeholder metrics with real numbers, or remove them.</li>
              <li>Check that dates, job titles and certifications are unchanged.</li>
              <li>Re-run the analysis after major edits to see the updated estimate.</li>
            </ul>
          </section>
        </div>
      </div>
    </section>
  )
}
