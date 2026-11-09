import React, { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, ScanSearch } from 'lucide-react'
import ResultsView from '../components/results/ResultsView.jsx'
import ErrorBanner from '../components/ui/ErrorBanner.jsx'
import PageLoader from '../components/ui/PageLoader.jsx'
import * as api from '../services/api.js'
import { getErrorMessage } from '../utils/errors.js'
import { formatDateTime } from '../utils/format.js'

export default function SavedAnalysisPage() {
  const { id } = useParams()
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    api.getAnalysis(id)
      .then((data) => {
        if (active) setDetail(data)
      })
      .catch((failure) => {
        if (active) setError(getErrorMessage(failure, 'This saved analysis could not be loaded.'))
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [id])

  if (loading) return <PageLoader label="Opening saved analysis…" />

  if (error || !detail) {
    return (
      <section className="saved-analysis-page">
        <ErrorBanner>{error || 'This saved analysis could not be found.'}</ErrorBanner>
        <Link className="button-secondary" to="/history"><ArrowLeft size={15} /> Back to history</Link>
      </section>
    )
  }

  const analysis = {
    comparison: detail.comparison || {},
    ats: detail.ats || {},
    suggestions: detail.suggestions || [],
    learning_paths: detail.learning_paths || [],
    interview: { role: detail.role || '', questions: [], tips: [] },
    structured_resume: {},
    resume_skills: [],
    job: {},
    meta: { saved: true },
    rewrite: null,
    rewriteError: '',
  }

  return (
    <section className="saved-analysis-page">
      <div className="saved-banner">
        <span className="record-icon"><ScanSearch size={16} /></span>
        <span>Saved snapshot · {formatDateTime(detail.created_at)}</span>
        <Link className="text-button" to="/history"><ArrowLeft size={15} /> All history</Link>
      </div>
      <ResultsView analysis={analysis} saved savedAt={formatDateTime(detail.created_at)} />
    </section>
  )
}
