import React, { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowLeft,
  BookmarkPlus,
  CheckCircle2,
  CircleHelp,
  LoaderCircle,
  MessageCircleQuestion,
  Send,
  ShieldCheck,
  Sparkles,
  Target,
} from 'lucide-react'
import EmptyState from '../components/ui/EmptyState.jsx'
import ErrorBanner from '../components/ui/ErrorBanner.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { useWorkspace } from '../context/WorkspaceContext.jsx'
import * as api from '../services/api.js'
import { interviewFromAnalysis } from '../utils/analysis.js'
import { getErrorMessage } from '../utils/errors.js'

export default function InterviewPage() {
  const { analysis, role } = useWorkspace()
  const { isAuthenticated } = useAuth()
  const interview = useMemo(() => interviewFromAnalysis(analysis), [analysis])
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [answer, setAnswer] = useState('')
  const [result, setResult] = useState(null)
  const [evaluating, setEvaluating] = useState(false)
  const [error, setError] = useState('')
  const [sessionId, setSessionId] = useState('')
  const [sessionBusy, setSessionBusy] = useState(false)
  const [sessionNote, setSessionNote] = useState('')

  const current = interview.questions[selectedIndex]

  if (!analysis || !interview.questions.length) {
    return (
      <EmptyState
        icon={MessageCircleQuestion}
        title="No interview questions yet"
        description="Run an analysis first. Questions are generated from the role, required skills and projects found in your resume."
        actionLabel="Run an analysis"
        actionTo="/analyze"
      />
    )
  }

  function selectQuestion(index) {
    setSelectedIndex(index)
    setAnswer('')
    setResult(null)
    setError('')
  }

  async function savePracticeSet() {
    if (!isAuthenticated || sessionId) return
    setSessionBusy(true)
    setSessionNote('')
    try {
      const saved = await api.saveInterview({
        role: interview.role || role || 'Practice set',
        questions: interview.questions.map((item) => ({
          id: item.id,
          category: item.category,
          question: item.question,
          difficulty: item.difficulty,
          related_skill: item.relatedSkill,
          expected_concepts: item.expectedConcepts,
          answer_framework: item.framework,
        })),
      })
      setSessionId(saved.id)
      setSessionNote('Practice set saved. Answers you evaluate will be stored with it.')
    } catch (failure) {
      setSessionNote(getErrorMessage(failure, 'The practice set could not be saved.'))
    } finally {
      setSessionBusy(false)
    }
  }

  async function evaluate(event) {
    event.preventDefault()
    if (!current || answer.trim().length < 20) {
      setError('Write at least a couple of sentences so the feedback has something to assess.')
      return
    }
    setEvaluating(true)
    setError('')
    setResult(null)
    const payload = {
      question: current.question,
      answer: answer.trim(),
      category: current.category,
      expected_concepts: current.expectedConcepts,
    }
    try {
      let feedback
      if (sessionId) {
        const response = await api.submitInterviewAnswer(sessionId, payload)
        feedback = response.feedback || response
      } else {
        feedback = await api.evaluateInterviewAnswer(payload)
      }
      setResult(feedback)
    } catch (failure) {
      setError(getErrorMessage(failure, 'The answer could not be evaluated. Check the API connection and try again.'))
    } finally {
      setEvaluating(false)
    }
  }

  return (
    <section className="interview-page">
      <div className="page-heading interview-heading">
        <div>
          <div className="eyebrow"><span className="eyebrow-line" /> PRACTICE OUT LOUD</div>
          <h1>Interview <span>prep.</span></h1>
          <p>Questions are grounded in {interview.role || role || 'your target role'} and the skills and projects found in your resume.</p>
        </div>
        <div className="interview-heading-actions">
          <Link className="button-secondary" to="/results"><ArrowLeft size={15} /> Back to results</Link>
          {isAuthenticated && (
            <button className="button-secondary" type="button" onClick={savePracticeSet} disabled={sessionBusy || Boolean(sessionId)}>
              {sessionBusy ? <LoaderCircle className="spin" size={15} /> : <BookmarkPlus size={15} />}
              {sessionId ? 'Practice set saved' : 'Save practice set'}
            </button>
          )}
        </div>
      </div>

      {sessionNote && <div className="editor-note" role="status"><ShieldCheck size={17} /><div><b>Practice history</b><span>{sessionNote}</span></div></div>}

      <div className="interview-layout">
        <aside className="question-list" aria-label="Interview questions">
          <div className="panel-kicker">QUESTION SET · {interview.questions.length}</div>
          {interview.questions.map((item, index) => (
            <button
              key={`${item.id}-${index}`}
              type="button"
              className={`question-list-item ${index === selectedIndex ? 'is-active' : ''}`}
              onClick={() => selectQuestion(index)}
            >
              <span className="question-number">{String(index + 1).padStart(2, '0')}</span>
              <span>
                <b>{item.question}</b>
                <small>{item.category} · {item.difficulty}</small>
              </span>
            </button>
          ))}
        </aside>

        <div className="interview-main">
          {current && (
            <section className="interview-question-card">
              <div className="question-meta">
                <span className="mini-badge">{current.category}</span>
                <span className="mini-badge">{current.difficulty}</span>
                {current.relatedSkill && <span className="mini-badge">Skill: {current.relatedSkill}</span>}
              </div>
              <h2>{current.question}</h2>
              {current.why && <p className="question-why"><CircleHelp size={15} /> {current.why}</p>}
              <div className="answer-framework">
                <b><Target size={14} /> Suggested structure</b>
                <p>{current.framework}</p>
              </div>
              {current.expectedConcepts.length > 0 && (
                <div className="expected-concepts">
                  <b>Concepts worth covering</b>
                  <div className="feature-tags">
                    {current.expectedConcepts.map((concept) => <span className="feature-tag" key={concept}>{concept}</span>)}
                  </div>
                </div>
              )}

              <form className="answer-form" onSubmit={evaluate}>
                <label htmlFor="interview-answer">Your answer</label>
                <textarea
                  id="interview-answer"
                  value={answer}
                  onChange={(event) => setAnswer(event.target.value)}
                  rows={8}
                  maxLength={10000}
                  placeholder="Describe a real situation, what you did, the trade-off you considered and the result."
                />
                <div className="answer-form-footer">
                  <span>{answer.trim() ? `${answer.trim().split(/\s+/).length} words` : 'Aim for a concrete example'}</span>
                  <button className="button-primary" type="submit" disabled={evaluating || answer.trim().length < 20}>
                    {evaluating ? <LoaderCircle className="spin" size={16} /> : <Send size={16} />}
                    {evaluating ? 'Reviewing…' : 'Review my answer'}
                  </button>
                </div>
              </form>
              {error && <ErrorBanner>{error}</ErrorBanner>}
            </section>
          )}

          {result && (
            <section className="interview-feedback" aria-live="polite">
              <div className="feedback-heading">
                <div>
                  <div className="panel-kicker">PRACTICE FEEDBACK</div>
                  <h2>Answer review</h2>
                </div>
                <div className="feedback-score">
                  <b>{result.score}</b><span>/ 100</span>
                </div>
              </div>
              <p className="feedback-text">{result.feedback}</p>
              <div className="feedback-metrics">
                <div><span>Question relevance</span><b>{result.relevance}%</b></div>
                <div><span>Words used</span><b>{result.word_count}</b></div>
              </div>
              <div className="feedback-columns">
                <div>
                  <h3><CheckCircle2 size={15} /> Concepts covered</h3>
                  <div className="feature-tags">
                    {result.covered_concepts?.length
                      ? result.covered_concepts.map((item) => <span className="feature-tag tag-match" key={item}>{item}</span>)
                      : <span className="feature-empty">No expected concepts were named explicitly.</span>}
                  </div>
                </div>
                <div>
                  <h3><Sparkles size={15} /> Concepts to add</h3>
                  <div className="feature-tags">
                    {result.missing_concepts?.length
                      ? result.missing_concepts.map((item) => <span className="feature-tag feature-tag-missing" key={item}>{item}</span>)
                      : <span className="feature-empty">No expected concepts were missed.</span>}
                  </div>
                </div>
              </div>
              {result.strengths?.length > 0 && (
                <div className="feedback-list">
                  <b>What worked</b>
                  <ul>{result.strengths.map((item) => <li key={item}>{item}</li>)}</ul>
                </div>
              )}
              {result.improvements?.length > 0 && (
                <div className="feedback-list">
                  <b>What to improve</b>
                  <ul>{result.improvements.map((item) => <li key={item}>{item}</li>)}</ul>
                </div>
              )}
              <p className="panel-footnote">{result.disclaimer || 'This is a keyword and structure heuristic, not a human interviewer’s judgement.'}</p>
            </section>
          )}
        </div>
      </div>

      {interview.tips.length > 0 && (
        <section className="interview-tips-panel">
          <div className="panel-heading">
            <div><span className="panel-kicker">PREPARE</span><h2>General tips for this role</h2></div>
            <MessageCircleQuestion size={19} />
          </div>
          <ul>{interview.tips.map((tip) => <li key={tip}>{tip}</li>)}</ul>
        </section>
      )}

      <p className="interview-disclaimer"><CircleHelp size={15} /> {interview.disclaimer}</p>
    </section>
  )
}
