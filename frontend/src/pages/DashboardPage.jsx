import React, { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  BriefcaseBusiness,
  FileText,
  History,
  MessageCircleQuestion,
  ScanSearch,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import PageLoader from '../components/ui/PageLoader.jsx'
import ErrorBanner from '../components/ui/ErrorBanner.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import * as api from '../services/api.js'
import { getErrorMessage } from '../utils/errors.js'
import { formatDate, pluralise } from '../utils/format.js'

const emptyData = { analyses: [], resumes: [], jobs: [], interviews: [] }

export default function DashboardPage() {
  const { user } = useAuth()
  const [data, setData] = useState(emptyData)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    async function load() {
      const results = await Promise.allSettled([
        api.listAnalyses(),
        api.listResumes(),
        api.listJobs(),
        api.listInterviews(),
      ])
      if (!active) return

      const [analyses, resumes, jobs, interviews] = results
      const rejected = results.find((result) => result.status === 'rejected')
      setData({
        analyses: analyses.status === 'fulfilled' ? analyses.value : [],
        resumes: resumes.status === 'fulfilled' ? resumes.value : [],
        jobs: jobs.status === 'fulfilled' ? jobs.value : [],
        interviews: interviews.status === 'fulfilled' ? interviews.value : [],
      })
      setError(rejected ? getErrorMessage(rejected.reason, 'Some dashboard data could not be loaded.') : '')
      setLoading(false)
    }

    load()
    return () => {
      active = false
    }
  }, [])

  const stats = useMemo(
    () => [
      { label: 'Saved analyses', value: data.analyses.length, icon: ScanSearch, to: '/history' },
      { label: 'Saved resumes', value: data.resumes.length, icon: FileText, to: '/history?tab=resumes' },
      { label: 'Saved roles', value: data.jobs.length, icon: BriefcaseBusiness, to: '/history?tab=jobs' },
      { label: 'Practice sets', value: data.interviews.length, icon: MessageCircleQuestion, to: '/history?tab=interviews' },
    ],
    [data],
  )

  if (loading) return <PageLoader label="Loading your workspace…" />

  const firstName = (user?.full_name || user?.email || '').split(/[\s@]/)[0]

  return (
    <section className="dashboard-page">
      <div className="page-heading dashboard-heading">
        <div>
          <div className="eyebrow"><span className="eyebrow-line" /> YOUR WORKSPACE</div>
          <h1>{firstName ? <>Welcome back, <span>{firstName}.</span></> : <>Your <span>workspace.</span></>}</h1>
          <p>Everything you save stays private to your account. Start a new analysis or pick up where you left off.</p>
        </div>
        <Link className="button-primary" to="/analyze"><ScanSearch size={16} /> New analysis</Link>
      </div>

      {error && <ErrorBanner>{error}</ErrorBanner>}

      <div className="stat-grid">
        {stats.map(({ label, value, icon: Icon, to }) => (
          <Link className="stat-card" to={to} key={label}>
            <span className="stat-icon"><Icon size={18} /></span>
            <b>{value}</b>
            <span>{label}</span>
          </Link>
        ))}
      </div>

      <div className="dashboard-grid">
        <section className="dashboard-panel">
          <div className="panel-heading">
            <div><span className="panel-kicker">RECENT WORK</span><h2>Saved analyses</h2></div>
            <Link className="text-button" to="/history">View all <ArrowRight size={15} /></Link>
          </div>
          {data.analyses.length ? (
            <ul className="record-list">
              {data.analyses.slice(0, 5).map((item) => (
                <li key={item.id}>
                  <Link className="record-row" to={`/analyses/${item.id}`}>
                    <span className="record-icon"><ScanSearch size={16} /></span>
                    <span className="record-copy">
                      <b>{item.role || 'Untitled role'}</b>
                      <small>{formatDate(item.created_at)}</small>
                    </span>
                    <ArrowRight size={15} />
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <div className="dashboard-empty">
              <p>No saved analyses yet. Run an analysis while signed in to keep a snapshot.</p>
              <Link className="button-secondary" to="/analyze">Analyze a resume <ArrowRight size={15} /></Link>
            </div>
          )}
        </section>

        <section className="dashboard-panel">
          <div className="panel-heading">
            <div><span className="panel-kicker">PRACTICE</span><h2>Recent interview sets</h2></div>
            <Link className="text-button" to="/history?tab=interviews">View all <ArrowRight size={15} /></Link>
          </div>
          {data.interviews.length ? (
            <ul className="record-list">
              {data.interviews.slice(0, 5).map((item) => (
                <li key={item.id}>
                  <Link className="record-row" to="/interview">
                    <span className="record-icon"><MessageCircleQuestion size={16} /></span>
                    <span className="record-copy">
                      <b>{item.role || 'Practice set'}</b>
                      <small>
                        {formatDate(item.created_at)} · {pluralise(item.question_count, 'question')}
                        {item.completed ? ' · completed' : ''}
                      </small>
                    </span>
                    <ArrowRight size={15} />
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <div className="dashboard-empty">
              <p>No saved practice sets yet. Generate questions from an analysis and save the set.</p>
              <Link className="button-secondary" to="/interview">Open interview prep <ArrowRight size={15} /></Link>
            </div>
          )}
        </section>
      </div>

      <div className="dashboard-actions">
        <Link className="action-card" to="/analyze">
          <span className="action-icon"><Sparkles size={19} /></span>
          <div><b>Run a new analysis</b><span>Compare one resume with one job posting.</span></div>
          <ArrowRight size={17} />
        </Link>
        <Link className="action-card" to="/jobs">
          <span className="action-icon"><BriefcaseBusiness size={19} /></span>
          <div><b>Compare several roles</b><span>Rank up to 25 postings with transparent components.</span></div>
          <ArrowRight size={17} />
        </Link>
        <Link className="action-card" to="/history">
          <span className="action-icon"><History size={19} /></span>
          <div><b>Review your history</b><span>Reopen, export or delete saved data.</span></div>
          <ArrowRight size={17} />
        </Link>
      </div>

      <p className="dashboard-privacy"><ShieldCheck size={15} /> Analyses are read-only snapshots. Resume text and rewrite drafts are not stored with them.</p>
    </section>
  )
}
