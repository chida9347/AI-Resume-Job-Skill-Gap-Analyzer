import React, { useRef, useState } from 'react'
import {
  ArrowDownToLine, ArrowLeft, ArrowRight, BadgeCheck, BriefcaseBusiness,
  Check, CheckCheck, ChevronRight, CircleHelp, FileText, LoaderCircle,
  PencilLine, RotateCcw, Sparkles, Target, X,
} from 'lucide-react'
import { jsPDF } from 'jspdf'
import ATSPanel from './components/ATSPanel.jsx'
import InterviewPreview from './components/InterviewPreview.jsx'
import JobInput from './components/JobInput.jsx'
import LearningPaths from './components/LearningPaths.jsx'
import ResumeRewrite from './components/ResumeRewrite.jsx'
import ResumeSignals from './components/ResumeSignals.jsx'
import SkillsSnapshot from './components/SkillsSnapshot.jsx'
import SuggestionsPanel from './components/SuggestionsPanel.jsx'
import UploadCard from './components/UploadCard.jsx'
import { analyzeResume, getAtsScore, getInterviewTips, getLearningPaths, rewriteForRole, updateResume } from './services/api.js'

const steps = ['Analyze', 'Insights', 'Edit resume', 'Interview prep']

function errorMessage(error, fallback) {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((item) => item.msg).filter(Boolean).join(', ') || fallback
  return fallback
}

function App() {
  const [page, setPage] = useState('home')
  const [file, setFile] = useState(null)
  const [jobDescription, setJobDescription] = useState('')
  const [role, setRole] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [resumeText, setResumeText] = useState('')
  const [atsResult, setAtsResult] = useState(null)
  const [atsSuggestions, setAtsSuggestions] = useState([])
  const [learningPaths, setLearningPaths] = useState([])
  const [rewriteResult, setRewriteResult] = useState(null)
  const [advancedLoading, setAdvancedLoading] = useState({ ats: false, learning: false, rewrite: false, interview: false })
  const [advancedErrors, setAdvancedErrors] = useState({ ats: '', learning: '', rewrite: '', interview: '' })
  const [appliedRewrite, setAppliedRewrite] = useState(false)
  const [appliedSkills, setAppliedSkills] = useState([])
  const [selected, setSelected] = useState([])
  const [tips, setTips] = useState(null)
  const [loading, setLoading] = useState(false)
  const [updating, setUpdating] = useState(false)
  const [error, setError] = useState('')
  const inputRef = useRef(null)

  async function loadAdvancedResults(resume, description, missingSkills, targetRole) {
    setAdvancedLoading({ ats: true, learning: true, rewrite: true, interview: true })
    setAdvancedErrors({ ats: '', learning: '', rewrite: '', interview: '' })
    const [ats, learning, rewrite, interview] = await Promise.allSettled([
      getAtsScore(resume, description),
      missingSkills.length ? getLearningPaths(missingSkills) : Promise.resolve([]),
      rewriteForRole(resume, description),
      getInterviewTips(targetRole || 'your target role'),
    ])
    setAtsResult(ats.status === 'fulfilled' ? ats.value : null)
    setAtsSuggestions(ats.status === 'fulfilled' ? ats.value.feedback
      .filter((item) => !item.startsWith('Missing important keyword:'))
      .map((text, index) => ({ id: `ats-feedback-${index}`, skill: 'ATS feedback', kind: 'review', text })) : [])
    setLearningPaths(learning.status === 'fulfilled' ? learning.value : [])
    setRewriteResult(rewrite.status === 'fulfilled' ? rewrite.value : null)
    setTips(interview.status === 'fulfilled' ? interview.value : {
      role: targetRole || 'your target role', questions: [], tips: [],
      error: errorMessage(interview.reason, 'Interview questions are unavailable.'),
    })
    setAdvancedErrors({
      ats: ats.status === 'rejected' ? errorMessage(ats.reason, 'ATS simulation is unavailable.') : '',
      learning: learning.status === 'rejected' ? errorMessage(learning.reason, 'Learning paths are unavailable.') : '',
      rewrite: rewrite.status === 'rejected' ? errorMessage(rewrite.reason, 'Resume rewrite is unavailable.') : '',
      interview: interview.status === 'rejected' ? errorMessage(interview.reason, 'Interview questions are unavailable.') : '',
    })
    setAdvancedLoading({ ats: false, learning: false, rewrite: false, interview: false })
  }

  function chooseFile(nextFile) {
    if (!nextFile) return
    const validType = /\.(pdf|docx)$/i.test(nextFile.name)
    if (!validType || nextFile.size > 10 * 1024 * 1024) {
      setError('Choose a PDF or DOCX file smaller than 10 MB.')
      return
    }
    setFile(nextFile)
    setError('')
  }

  async function runAnalysis(event) {
    event.preventDefault()
    if (!file || jobDescription.trim().length < 40) {
      setError(!file ? 'Add your resume to get started.' : 'Add a little more detail to the job description.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const result = await analyzeResume(file, jobDescription)
      setAnalysis(result)
      setResumeText(result.resume.extracted_text)
      setSelected([])
      setAppliedRewrite(false)
      setAppliedSkills([])
      setAtsResult(null)
      setAtsSuggestions([])
      setLearningPaths([])
      setRewriteResult(null)
      setTips(null)
      setPage('results')
      void loadAdvancedResults(result.resume.extracted_text, jobDescription, result.comparison.missing_skills, role)
    } catch (requestError) {
      const message = requestError.response?.data?.detail
      setError(typeof message === 'string' ? message : 'Could not reach the analyzer. Check that the API is running, then try again.')
    } finally {
      setLoading(false)
    }
  }

  function toggleSuggestion(id) {
    setSelected((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id])
  }

  async function applySuggestions() {
    setUpdating(true)
    setError('')
    try {
      const selectedItems = [...(analysis?.suggestions || []), ...atsSuggestions]
        .filter((item) => selected.includes(item.id))
      const confirmedSkills = selectedItems.filter((item) => item.kind === 'skill').map((item) => item.skill)
      const reviewNotes = selectedItems.filter((item) => item.kind !== 'skill').map((item) => item.text)
      setResumeText(await updateResume(resumeText, reviewNotes, confirmedSkills))
      setAppliedSkills(confirmedSkills)
      setPage('editor')
    } catch {
      setError('Could not update the resume. Check the API connection and try again.')
    } finally {
      setUpdating(false)
    }
  }

  function applyRewrite() {
    if (!rewriteResult?.rewritten) return
    setResumeText(rewriteResult.rewritten)
    setAppliedRewrite(true)
    setPage('editor')
  }

  function downloadTextAsPdf(text, filename, targetRole = '') {
    if (!text?.trim()) return
    const pdf = new jsPDF({ unit: 'pt', format: 'letter' })
    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()
    const margin = 54
    const contentWidth = pageWidth - margin * 2
    const sourceLines = text.replace(/\r/g, '').split('\n')
    const firstContentIndex = sourceLines.findIndex((line) => line.trim())
    const headingPattern = /^\s*((?:(?:professional|technical)\s+)?(?:summary|profile|objective|experience|employment history|work history|skills|education|certifications?|projects?|awards?))\s*:?\s*(.*)$/i
    let name = 'Resume'

    if (firstContentIndex >= 0 && !headingPattern.test(sourceLines[firstContentIndex])) {
      name = sourceLines[firstContentIndex].trim()
      sourceLines.splice(firstContentIndex, 1)
    }

    const preamble = []
    const sections = []
    let currentSection = null
    for (const line of sourceLines) {
      const heading = line.match(headingPattern)
      if (heading) {
        currentSection = { title: heading[1].trim(), lines: [] }
        sections.push(currentSection)
        if (heading[2].trim()) currentSection.lines.push(heading[2].trim())
      } else if (currentSection) {
        currentSection.lines.push(line)
      } else if (line.trim()) {
        preamble.push(line.trim())
      }
    }

    pdf.setDrawColor(36, 75, 62)
    pdf.setLineWidth(3)
    pdf.line(margin, 35, pageWidth - margin, 35)
    let y = 70
    pdf.setTextColor(24, 33, 31)
    pdf.setFont('helvetica', 'bold')
    pdf.setFontSize(23)
    pdf.text(name, margin, y)
    y += 18

    if (targetRole.trim()) {
      pdf.setTextColor(87, 105, 82)
      pdf.setFont('helvetica', 'normal')
      pdf.setFontSize(9)
      pdf.text(`TARGET ROLE  |  ${targetRole.trim()}`, margin, y)
      y += 15
    }

    if (preamble.length) {
      pdf.setTextColor(91, 99, 93)
      pdf.setFont('helvetica', 'normal')
      pdf.setFontSize(9)
      for (const line of preamble) {
        const wrapped = pdf.splitTextToSize(line, contentWidth)
        for (const row of wrapped) {
          pdf.text(row, margin, y)
          y += 12
        }
      }
    }

    y += 4
    pdf.setDrawColor(218, 222, 212)
    pdf.setLineWidth(0.7)
    pdf.line(margin, y, pageWidth - margin, y)
    y += 18

    function ensureSpace(height) {
      if (y + height > pageHeight - 48) {
        pdf.addPage()
        y = 52
      }
    }

    function writeBodyLine(rawLine, isExperience = false) {
      const trimmed = rawLine.trim()
      if (!trimmed) {
        y += 5
        return
      }
      const bulletMatch = trimmed.match(/^(?:[-*+]\s+|\d+[.)]\s+)(.*)$/)
      const accomplishment = /^(?:built|created|developed|designed|implemented|delivered|led|launched|improved|increased|reduced|optimized|automated|analyzed|managed|maintained|migrated|deployed|engineered|generated|established|streamlined|resolved|integrated|collaborated|supported|configured|tested|wrote|conducted|coordinated|owned|mentored|achieved|introduced)\b/i.test(trimmed)
      const isBullet = Boolean(bulletMatch) || (isExperience && accomplishment)
      const content = bulletMatch ? bulletMatch[1] : trimmed
      const indent = isBullet ? 14 : 0
      const rows = pdf.splitTextToSize(content, contentWidth - indent)
      pdf.setFont('helvetica', 'normal')
      pdf.setFontSize(10)
      pdf.setTextColor(45, 53, 48)
      for (let index = 0; index < rows.length; index += 1) {
        ensureSpace(14)
        if (isBullet && index === 0) {
          pdf.setFillColor(119, 148, 72)
          pdf.circle(margin + 3, y - 3, 1.6, 'F')
        }
        pdf.text(rows[index], margin + indent, y)
        y += 14
      }
    }

    for (const section of sections) {
      if (!section.lines.some((line) => line.trim())) continue
      ensureSpace(34)
      pdf.setFont('helvetica', 'bold')
      pdf.setFontSize(11)
      pdf.setTextColor(36, 75, 62)
      pdf.text(section.title.toUpperCase(), margin, y)
      y += 7
      pdf.setDrawColor(221, 226, 215)
      pdf.setLineWidth(0.6)
      pdf.line(margin, y, pageWidth - margin, y)
      y += 14
      const isExperience = /experience|employment history|work history/i.test(section.title)
      for (const line of section.lines) writeBodyLine(line, isExperience)
      y += 7
    }

    if (!sections.length) {
      for (const line of preamble) writeBodyLine(line)
    }

    const pageCount = pdf.getNumberOfPages()
    for (let pageNumber = 1; pageNumber <= pageCount; pageNumber += 1) {
      pdf.setPage(pageNumber)
      pdf.setFont('helvetica', 'normal')
      pdf.setFontSize(8)
      pdf.setTextColor(126, 133, 125)
      pdf.text(`${name}  |  ${pageNumber}`, pageWidth - margin, pageHeight - 24, { align: 'right' })
    }

    const downloadUrl = URL.createObjectURL(pdf.output('blob'))
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename
    link.style.display = 'none'
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000)
  }

  function downloadResume() {
    downloadTextAsPdf(resumeText, 'updated-resume.pdf', role)
  }

  async function openInterview() {
    setPage('interview')
    if (tips || advancedLoading.interview) return
    try {
      setTips(await getInterviewTips(role || 'your target role'))
    } catch {
      setTips({ role: role || 'your target role', questions: [], tips: [], error: 'Interview tips are unavailable. Check the API connection.' })
    }
  }

  function startOver() {
    setAnalysis(null)
    setFile(null)
    setJobDescription('')
    setResumeText('')
    setAtsResult(null)
    setAtsSuggestions([])
    setLearningPaths([])
    setRewriteResult(null)
    setAppliedRewrite(false)
    setAppliedSkills([])
    setTips(null)
    setSelected([])
    setError('')
    setPage('upload')
  }

  const activeStep = page === 'upload' || page === 'home' ? 0 : ['results', 'editor', 'interview'].indexOf(page) + 1

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="wordmark" onClick={() => setPage('home')} aria-label="Roleprint home">
          <span className="brand-mark"><Target size={19} strokeWidth={2.4} /></span>
          <span>roleprint<span className="brand-period">.</span></span>
        </button>
        <div className="topbar-right">
          <span className="privacy-note"><span className="privacy-dot" /> Private by design</span>
          {analysis && <button className="text-button" onClick={startOver}><RotateCcw size={15} /> New analysis</button>}
        </div>
      </header>

      {page !== 'home' && <nav className="step-nav" aria-label="Analysis progress">
        {steps.map((step, index) => <button key={step} className={`step-item ${index === activeStep ? 'is-active' : ''} ${index < activeStep ? 'is-done' : ''}`} onClick={() => {
          if (index === 0) setPage('upload')
          if (index === 1 && analysis) setPage('results')
          if (index === 2 && analysis) setPage('editor')
          if (index === 3 && analysis) openInterview()
        }} disabled={index > 0 && !analysis}>
          <span className="step-number">{index < activeStep ? <Check size={13} /> : `0${index + 1}`}</span><span>{step}</span>
        </button>)}
      </nav>}

      <main className={`main-content ${page === 'home' ? 'main-home' : ''}`}>
        {page === 'home' && <section className="hero">
          <div className="hero-copy">
            <div className="eyebrow"><span className="eyebrow-line" /> AI RESUME ANALYZER</div>
            <h1>AI Resume<br /><span>Analyzer.</span></h1>
            <p className="hero-lede">Optimize your resume for any job in seconds.</p>
            <button className="button-primary hero-cta" onClick={() => setPage('upload')}>Analyze Resume <ArrowRight size={17} /></button>
            <div className="hero-proof"><span><CheckCheck size={15} /> Skill-by-skill match</span><i /> <span><FileText size={15} /> Your data stays yours</span></div>
          </div>
          <div className="hero-visual" aria-hidden="true">
            <div className="visual-orbit orbit-one" /><div className="visual-orbit orbit-two" />
            <div className="visual-paper">
              <div className="paper-top"><span className="paper-avatar">JD</span><div><b>Jordan Davis</b><span>PRODUCT DESIGNER</span></div><BadgeCheck size={17} className="verified-icon" /></div>
              <div className="paper-rule" /><div className="paper-label">YOUR EXPERIENCE, AT A GLANCE</div>
              <div className="paper-skill-row"><span>Product strategy</span><span className="mini-match">MATCH</span></div>
              <div className="paper-skill-row"><span>Design systems</span><span className="mini-match">MATCH</span></div>
              <div className="paper-skill-row"><span>Data storytelling</span><span className="mini-gap">EXPLORE</span></div>
              <div className="paper-meter"><div className="meter-copy"><span>ROLE ALIGNMENT</span><b>78%</b></div><div className="meter-track"><i /></div></div>
              <div className="paper-note"><Sparkles size={14} /><span>A clearer picture of what to highlight.</span></div>
            </div>
            <div className="float-stamp stamp-match"><span className="stamp-dot" /> Good alignment</div>
            <div className="float-stamp stamp-skill"><span className="stamp-plus">+</span> Skill insight</div>
            <div className="visual-caption">YOUR NEXT CHAPTER, IN FOCUS <span>01 / 04</span></div>
          </div>
          <div className="hero-bottom"><span>BUILT FOR THE IN-BETWEEN</span><span>Know what fits. See what’s next.</span><ArrowRight size={16} /></div>
        </section>}

        {page === 'upload' && <section className="workflow-page">
          <div className="page-heading"><div className="eyebrow"><span className="eyebrow-line" /> START WITH THE DETAILS</div><h1>Bring the role<br />into <span>focus.</span></h1><p>Share your resume and the job posting. We’ll map the overlap and show you where to focus next.</p></div>
          <form className="input-layout grid" onSubmit={runAnalysis}>
            <UploadCard file={file} inputRef={inputRef} onFileSelect={chooseFile} />
            <JobInput role={role} onRoleChange={setRole} description={jobDescription} onDescriptionChange={setJobDescription} />
            <div className="form-footer">
              <div className="error-slot" role="alert">{error && <><CircleHelp size={15} /> {error}</>}</div>
              <button type="submit" className="button-primary" disabled={loading}>{loading ? <><LoaderCircle className="spin" size={17} /> Reading your documents…</> : <>See the match <ArrowRight size={17} /></>}</button>
            </div>
          </form>
        </section>}

        {page === 'results' && analysis && <section className="results-page">
              <div className="results-heading"><div><div className="eyebrow"><span className="eyebrow-line" /> YOUR RESULTS</div><h1>Resume <span>analysis.</span></h1><p>We found {analysis.comparison.matched_skills.length} of {analysis.comparison.matched_skills.length + analysis.comparison.missing_skills.length} requested skills in your resume. A missing skill means it was not found in the resume text.</p></div><div className="results-metrics"><div className="score-block"><div className="score-value">{analysis.comparison.similarity_score}<span>%</span></div><div className="score-label">SKILL MATCH</div><div className="score-track"><i style={{ width: `${analysis.comparison.similarity_score}%` }} /></div></div><div className="score-block ats-top-score"><div className="score-value">{atsResult ? atsResult.ats_score : advancedLoading.ats ? '…' : '--'}<span>{atsResult ? '/100' : ''}</span></div><div className="score-label">ATS ESTIMATE</div><div className="score-hint">Keywords + sections + format</div></div></div></div>
          <div className="results-grid grid">
            <SkillsSnapshot comparison={analysis.comparison} />
            <SuggestionsPanel suggestions={[...(analysis.suggestions || []), ...atsSuggestions]} selected={selected} onToggle={toggleSuggestion} onReview={applySuggestions} updating={updating} error={error} />
            <ResumeSignals comparison={analysis.comparison} onInterview={openInterview} />
          </div>
          <div className="advanced-features grid" aria-label="Advanced analysis">
            <ATSPanel result={atsResult} loading={advancedLoading.ats} error={advancedErrors.ats} />
            <ResumeRewrite result={rewriteResult} loading={advancedLoading.rewrite} error={advancedErrors.rewrite} onApply={applyRewrite} onDownload={() => downloadTextAsPdf(rewriteResult?.rewritten, 'rewritten-resume.pdf', role)} applying={false} />
            <LearningPaths paths={learningPaths} loading={advancedLoading.learning} error={advancedErrors.learning} hasGaps={analysis.comparison.missing_skills.length > 0} />
          </div>
          <InterviewPreview tips={tips} loading={advancedLoading.interview} error={advancedErrors.interview} onOpen={openInterview} />
          <div className="results-bottom"><span>Made from your resume and this job description.</span><button className="text-button" onClick={() => setPage('upload')}><ArrowLeft size={15} /> Edit inputs</button></div>
        </section>}

        {page === 'editor' && analysis && <section className="editor-page">
          <div className="page-heading compact-heading"><div className="eyebrow"><span className="eyebrow-line" /> MAKE IT YOURS</div><h1>Shape the <span>story.</span></h1><p>Your resume text is editable. Review each change before you export it.</p></div>
          {appliedSkills.length > 0 && <div className="editor-note"><Sparkles size={17} /><div><b>Confirmed skills added to the resume</b><span>Added to Skills: {appliedSkills.join(', ')}. Keep only skills that accurately describe your experience.</span></div></div>}
          {selected.some((item) => !appliedSkills.includes(item)) && <div className="editor-note"><Sparkles size={17} /><div><b>Other selections added as review notes</b><span>Review these prompts and edit or remove anything that does not reflect your experience.</span></div></div>}
          {appliedRewrite && <div className="editor-note"><Sparkles size={17} /><div><b>Role-specific draft applied</b><span>Review each change for accuracy. Replace metric prompts with verified results before downloading.</span></div></div>}
          {error && <p className="error-banner" role="alert">{error}</p>}
          <div className="editor-toolbar"><span><PencilLine size={16} /> RESUME TEXT</span><span>{resumeText.trim().split(/\s+/).filter(Boolean).length} words</span></div>
          <textarea className="resume-editor" value={resumeText} onChange={(event) => setResumeText(event.target.value)} aria-label="Editable resume text" />
          <div className="editor-actions"><button className="button-secondary" onClick={() => setPage('results')}><ArrowLeft size={16} /> Back to insights</button><button className="button-primary" onClick={downloadResume}><ArrowDownToLine size={17} /> Download updated resume PDF</button></div>
        </section>}

        {page === 'interview' && <section className="interview-page">
          <div className="page-heading compact-heading"><div className="eyebrow"><span className="eyebrow-line" /> BEFORE YOU WALK IN</div><h1>Practice with <span>purpose.</span></h1><p>Start with useful prompts, then make every answer your own.</p></div>
          {!tips ? <div className="tips-loading"><LoaderCircle className="spin" size={19} /> Preparing prompts…</div> : tips.error ? <p className="error-banner">{tips.error}</p> : <>
            <div className="interview-role"><BriefcaseBusiness size={17} /><span>Interview prep for</span><b>{tips.role}</b></div>
            <div className="question-list">{tips.questions.map((item, index) => <article className="question-row" key={item.question}><span className="question-index">0{index + 1}</span><div><h2>{item.question}</h2><div className="answer-label">A FRAMEWORK TO ADAPT</div><p>{item.example_answer}</p></div><ChevronRight size={18} className="question-chevron" /></article>)}</div>
            <section className="prep-tips"><div className="prep-heading"><Sparkles size={17} /><h2>Keep in mind</h2></div><div className="prep-tip-list">{tips.tips.map((tip) => <div className="prep-tip" key={tip}><Check size={15} />{tip}</div>)}</div></section>
          </>}
          <button className="text-button interview-back" onClick={() => setPage('results')}><ArrowLeft size={15} /> Back to your analysis</button>
        </section>}
      </main>
      <footer className="site-footer"><span>ROLEPRINT <i>·</i> CAREER TOOLS, WITH CLARITY</span><span>Useful guidance. Your decisions.</span></footer>
    </div>
  )
}

export default App