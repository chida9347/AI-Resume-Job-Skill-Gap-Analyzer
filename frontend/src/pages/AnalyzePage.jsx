import React, { useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight, CircleHelp, FileText, LoaderCircle, LockKeyhole, Sparkles } from 'lucide-react'
import UploadCard from '../components/UploadCard.jsx'
import JobInput from '../components/JobInput.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { useWorkspace } from '../context/WorkspaceContext.jsx'

const MIN_JOB_LENGTH = 40
const MIN_RESUME_LENGTH = 40

export default function AnalyzePage() {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()
  const {
    file,
    jobDescription,
    role,
    busy,
    progress,
    error,
    analysis,
    setFile,
    setJobDescription,
    setRole,
    runAnalysis,
  } = useWorkspace()
  const inputRef = useRef(null)
  const [mode, setMode] = useState('upload')
  const [pastedResume, setPastedResume] = useState('')
  const [saveHistory, setSaveHistory] = useState(true)
  const [localError, setLocalError] = useState('')

  function chooseFile(nextFile) {
    if (!nextFile) return
    const validType = /\.(pdf|docx)$/i.test(nextFile.name)
    if (!validType || nextFile.size > 10 * 1024 * 1024) {
      setLocalError('Choose a PDF or DOCX file smaller than 10 MB.')
      return
    }
    setLocalError('')
    setFile(nextFile)
  }

  async function submit(event) {
    event.preventDefault()
    setLocalError('')
    if (mode === 'upload' && !file) {
      setLocalError('Add your resume to get started.')
      return
    }
    if (mode === 'paste' && pastedResume.trim().length < MIN_RESUME_LENGTH) {
      setLocalError('Paste a little more resume text so the analysis has enough to work with.')
      return
    }
    if (jobDescription.trim().length < MIN_JOB_LENGTH) {
      setLocalError('Add a little more detail to the job description.')
      return
    }
    try {
      await runAnalysis({
        file: mode === 'upload' ? file : null,
        resumeText: mode === 'paste' ? pastedResume : '',
        jobDescription,
        role,
        saveToHistory: isAuthenticated && saveHistory,
      })
      navigate('/results')
    } catch {
      // The workspace stores a user-facing error message.
    }
  }

  const pasteWords = pastedResume.trim() ? pastedResume.trim().split(/\s+/).length : 0

  return (
    <section className="workflow-page">
      <div className="page-heading">
        <div className="eyebrow"><span className="eyebrow-line" /> START WITH THE DETAILS</div>
        <h1>Bring the role<br />into <span>focus.</span></h1>
        <p>Share your resume and the job posting. We’ll map the overlap and show you where to focus next.</p>
      </div>

      {analysis && (
        <div className="editor-note" role="status">
          <Sparkles size={17} />
          <div>
            <b>You already have a current analysis</b>
            <span>
              <Link to="/results">Open the results</Link> or run a new comparison below. Running a new analysis replaces the current workspace result.
            </span>
          </div>
        </div>
      )}

      <form className="input-layout grid" onSubmit={submit}>
        <section className="input-section upload-card">
          <div className="input-mode-tabs" role="tablist" aria-label="Resume input method">
            <button
              type="button"
              role="tab"
              aria-selected={mode === 'upload'}
              className={mode === 'upload' ? 'is-active' : ''}
              onClick={() => setMode('upload')}
            >
              <FileText size={14} /> Upload file
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={mode === 'paste'}
              className={mode === 'paste' ? 'is-active' : ''}
              onClick={() => setMode('paste')}
            >
              <Sparkles size={14} /> Paste text
            </button>
          </div>

          {mode === 'upload' ? (
            <UploadCard file={file} inputRef={inputRef} onFileSelect={chooseFile} />
          ) : (
            <>
              <div className="section-heading">
                <span className="section-index">01</span>
                <div><h2>Your resume text</h2><p>Paste the text exactly as it appears in your document</p></div>
              </div>
              <textarea
                className="job-textarea resume-paste"
                value={pastedResume}
                onChange={(event) => setPastedResume(event.target.value)}
                placeholder={'Paste your resume text here...\n\nInclude your summary, skills, experience, education and projects.'}
                maxLength={100000}
                aria-label="Resume text"
              />
              <div className="textarea-footer">
                <span>Nothing is saved unless you choose to save it</span>
                <span>{pasteWords.toLocaleString()} words</span>
              </div>
            </>
          )}
        </section>

        <JobInput role={role} onRoleChange={setRole} description={jobDescription} onDescriptionChange={setJobDescription} />

        {isAuthenticated && (
          <label className="save-history-option">
            <input type="checkbox" checked={saveHistory} onChange={(event) => setSaveHistory(event.target.checked)} />
            <span><LockKeyhole size={14} /> Save this resume, job and analysis to my private history</span>
          </label>
        )}

        <div className="form-footer">
          <div className="error-slot" role="alert">
            {(localError || error) && <><CircleHelp size={15} /> {localError || error}</>}
          </div>
          <div className="form-footer-actions">
            {busy && progress > 0 && <span className="progress-note">{progress}%</span>}
            <button type="submit" className="button-primary" disabled={busy}>
              {busy
                ? <><LoaderCircle className="spin" size={17} /> {progress >= 60 ? 'Comparing documents…' : 'Reading your documents…'}</>
                : <>See the match <ArrowRight size={17} /></>}
            </button>
          </div>
        </div>
      </form>
    </section>
  )
}
