import React, { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  BookOpenCheck,
  BriefcaseBusiness,
  FileText,
  History,
  MessageCircleQuestion,
  ScanSearch,
  Settings,
  ShieldCheck,
} from 'lucide-react'
import PageLoader from '../components/ui/PageLoader.jsx'
import ErrorBanner from '../components/ui/ErrorBanner.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import * as api from '../services/api.js'
import { getErrorMessage } from '../utils/errors.js'
import { formatDate, pluralise } from '../utils/format.js'

const emptyData = { analyses: [], resumes: [], jobs: [], interviews: [] }

function greetingFor(hour) {
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
}

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
      { label: 'Saved analyses', value: data.analyses.length, icon: ScanSearch, to: '/history', hint: 'Read-only snapshots' },
      { label: 'Resumes', value: data.resumes.length, icon: FileText, to: '/history?tab=resumes', hint: 'Stored privately' },
      { label: 'Roles', value: data.jobs.length, icon: BriefcaseBusiness, to: '/history?tab=jobs', hint: 'Saved job posts' },
      { label: 'Practice sets', value: data.interviews.length, icon: MessageCircleQuestion, to: '/history?tab=interviews', hint: 'Interview questions' },
    ],
    [data],
  )

  if (loading) return <PageLoader label="Loading your workspace..." />

  const firstName = (user?.full_name || user?.email || '').split(/[\s@]/)[0]
  const latest = data.analyses[0]
  const today = new Date().toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' })

  return (
    <section className="dashboard-page">
      {error && <ErrorBanner>{error}</ErrorBanner>}

      <div className="dash-hero">
        <div className="dash-hero-copy">
          <span className="dash-date">{today}</span>
          <h1>{greetingFor(new Date().getHours())}, <span>{firstName || 'there'}.</span></h1>
          <p>Start a fresh comparison, line up several roles, or reopen one of your saved snapshots.</p>
          <div className="dash-hero-actions">
            <Link className="button-primary" to="/analyze"><ScanSearch size={16} /> Start a new analysis</Link>
            <Link className="button-secondary" to="/jobs"><BriefcaseBusiness size={16} /> Compare roles</Link>
          </div>
        </div>

        <div className="dash-hero-card">
          {latest ? (
            <>
              <span className="dash-card-label">LATEST ANALYSIS</span>
              <b>{latest.role || 'Untitled role'}</b>
              <span className="dash-card-meta">{formatDate(latest.created_at)}</span>
              <Link className="dash-card-link" to={`/analyses/${latest.id}`}>
                Open snapshot <ArrowRight size={15} />
              </Link>
            </>
          ) : (
            <>
              <span className="dash-card-label">GET STARTED</span>
              <ol className="dash-checklist">
                <li><span>1</span> Add your resume</li>
                <li><span>2</span> Paste a job description</li>
                <li><span>3</span> Read the evidence</li>
              </ol>
              <Link className="dash-card-link" to="/analyze">
                Run your first analysis <ArrowRight size={15} />
              </Link>
            </>
          )}
        </div>
      </div>

      <div className="dash-stats">
        {stats.map(({ label, value, icon: Icon, to, hint }) => (
          <Link className="dash-stat" to={to} key={label}>
            <span className="dash-stat-icon"><Icon size={18} /></span>
            <b>{value}</b>
            <span className="dash-stat-label">{label}</span>
            <small>{hint}</small>
          </Link>
        ))}
      </div>

      <div className="dash-columns">
        <section className="dash-panel dash-recent">
          <header className="dash-panel-head">
            <div><span className="panel-kicker">RECENT WORK</span><h2>Saved analyses</h2></div>
            <Link className="text-button" to="/history">View all <ArrowRight size={15} /></Link>
          </header>
          {data.analyses.length ? (
            <ul className="dash-record-list">
              {data.analyses.slice(0, 5).map((item) => (
                <li key={item.id}>
                  <Link className="dash-record" to={`/analyses/${item.id}`}>
                    <span className="dash-record-icon"><ScanSearch size={16} /></span>
                    <span className="dash-record-copy">
                      <b>{item.role || 'Untitled role'}</b>
                      <small>{formatDate(item.created_at)}</small>
                    </span>
                    <span className="dash-record-badge">Snapshot</span>
                    <ArrowRight size={15} />
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <div className="dash-empty">
              <span className="dash-empty-icon"><History size={20} /></span>
              <div>
                <b>No saved analyses yet</b>
                <p>Run an analysis and keep the report in your private history.</p>
              </div>
              <Link className="button-secondary" to="/analyze">Analyze a resume <ArrowRight size={15} /></Link>
            </div>
          )}
        </section>

        <aside className="dash-side">
          <section className="dash-panel">
            <header className="dash-panel-head">
              <div><span className="panel-kicker">PRACTICE</span><h2>Recent sets</h2></div>
              <Link className="text-button" to="/history?tab=interviews">View all</Link>
            </header>
            {data.interviews.length ? (
              <ul className="dash-mini-list">
                {data.interviews.slice(0, 3).map((item) => (
                  <li key={item.id}>
                    <Link to="/interview">
                      <span className="dash-record-icon"><MessageCircleQuestion size={15} /></span>
                      <span>
                        <b>{item.role || 'Practice set'}</b>
                        <small>{pluralise(item.question_count, 'question')}{item.completed ? ' · completed' : ''}</small>
                      </span>
                      <ArrowRight size={14} />
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="dash-muted">No practice sets yet. Generate questions from a live analysis.</p>
            )}
          </section>

          <section className="dash-panel dash-links">
            <span className="panel-kicker">SHORTCUTS</span>
            <Link to="/interview"><MessageCircleQuestion size={16} /> Interview prep <ArrowRight size={15} /></Link>
            <Link to="/roadmap"><BookOpenCheck size={16} /> Learning roadmap <ArrowRight size={15} /></Link>
            <Link to="/settings"><Settings size={16} /> Privacy &amp; data <ArrowRight size={15} /></Link>
          </section>
        </aside>
      </div>

      <p className="dash-privacy"><ShieldCheck size={15} /> Analyses are read-only snapshots. Resume text and rewrite drafts are not stored with them.</p>
    </section>
  )
}
