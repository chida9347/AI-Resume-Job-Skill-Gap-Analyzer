import React, { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  ArrowRight,
  BriefcaseBusiness,
  FileText,
  LoaderCircle,
  MessageCircleQuestion,
  ScanSearch,
  Trash2,
} from 'lucide-react'
import ConfirmDialog from '../components/ui/ConfirmDialog.jsx'
import EmptyState from '../components/ui/EmptyState.jsx'
import ErrorBanner from '../components/ui/ErrorBanner.jsx'
import PageLoader from '../components/ui/PageLoader.jsx'
import * as api from '../services/api.js'
import { getErrorMessage } from '../utils/errors.js'
import { formatDate, pluralise } from '../utils/format.js'

const tabs = [
  { id: 'analyses', label: 'Analyses', icon: ScanSearch },
  { id: 'resumes', label: 'Resumes', icon: FileText },
  { id: 'jobs', label: 'Roles', icon: BriefcaseBusiness },
  { id: 'interviews', label: 'Practice sets', icon: MessageCircleQuestion },
]

const loaders = {
  analyses: api.listAnalyses,
  resumes: api.listResumes,
  jobs: api.listJobs,
  interviews: api.listInterviews,
}

const deleters = {
  analyses: api.deleteAnalysis,
  resumes: api.deleteResume,
  jobs: api.deleteJob,
  interviews: api.deleteInterview,
}

export default function HistoryPage() {
  const [params, setParams] = useSearchParams()
  const tabParam = params.get('tab')
  const activeTab = tabs.some((tab) => tab.id === tabParam) ? tabParam : 'analyses'
  const [data, setData] = useState({ analyses: [], resumes: [], jobs: [], interviews: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [pending, setPending] = useState(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    let active = true
    async function load() {
      setLoading(true)
      const results = await Promise.allSettled(tabs.map((tab) => loaders[tab.id]()))
      if (!active) return
      const next = { analyses: [], resumes: [], jobs: [], interviews: [] }
      results.forEach((result, index) => {
        if (result.status === 'fulfilled') next[tabs[index].id] = result.value
      })
      setData(next)
      const rejected = results.find((result) => result.status === 'rejected')
      setError(rejected ? getErrorMessage(rejected.reason, 'Some saved history could not be loaded.') : '')
      setLoading(false)
    }
    load()
    return () => {
      active = false
    }
  }, [])

  const items = data[activeTab] || []
  const activeLabel = tabs.find((tab) => tab.id === activeTab)?.label || 'items'

  const description = useMemo(() => {
    if (!pending) return ''
    if (pending.tab === 'analyses') return `Delete the saved analysis for “${pending.item.role || 'Untitled role'}”? This cannot be undone.`
    if (pending.tab === 'resumes') return `Delete the saved resume “${pending.item.filename}”? This cannot be undone.`
    if (pending.tab === 'jobs') return `Delete the saved role “${pending.item.title || pending.item.company || 'Untitled role'}”? This cannot be undone.`
    return `Delete the practice set for “${pending.item.role || 'Untitled role'}”? This cannot be undone.`
  }, [pending])

  async function confirmDelete() {
    if (!pending) return
    setDeleting(true)
    try {
      await deleters[pending.tab](pending.item.id)
      setData((current) => ({ ...current, [pending.tab]: current[pending.tab].filter((item) => item.id !== pending.item.id) }))
      setPending(null)
    } catch (failure) {
      setError(getErrorMessage(failure, 'The item could not be deleted.'))
    } finally {
      setDeleting(false)
    }
  }

  if (loading) return <PageLoader label="Loading saved history…" />

  return (
    <section className="history-page">
      <div className="page-heading history-heading">
        <div>
          <div className="eyebrow"><span className="eyebrow-line" /> SAVED HISTORY</div>
          <h1>Your <span>archive.</span></h1>
          <p>Everything here belongs to your account. Delete individual items or clear all history from Settings.</p>
        </div>
        <Link className="button-primary" to="/analyze"><ScanSearch size={16} /> New analysis</Link>
      </div>

      <div className="history-tabs" role="tablist" aria-label="History type">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={activeTab === id}
            className={`history-tab ${activeTab === id ? 'is-active' : ''}`}
            onClick={() => {
              if (id === 'analyses') setParams({})
              else setParams({ tab: id })
            }}
          >
            <Icon size={15} /> {label}
            <span className="count-pill">{data[id].length}</span>
          </button>
        ))}
      </div>

      {error && <ErrorBanner>{error}</ErrorBanner>}

      {items.length === 0 ? (
        <EmptyState
          icon={activeTab === 'interviews' ? MessageCircleQuestion : activeTab === 'jobs' ? BriefcaseBusiness : FileText}
          title={`No saved ${activeLabel.toLowerCase()} yet`}
          description={
            activeTab === 'analyses'
              ? 'Run an analysis while signed in and choose to save it to your private history.'
              : activeTab === 'interviews'
                ? 'Open interview prep and save a practice set to keep it here.'
                : 'Saved items will appear here after you run an analysis while signed in.'
          }
          actionLabel={activeTab === 'interviews' ? 'Open interview prep' : 'Run an analysis'}
          actionTo={activeTab === 'interviews' ? '/interview' : '/analyze'}
        />
      ) : (
        <ul className="history-list">
          {items.map((item) => (
            <li className="history-row" key={item.id}>
              <div className="history-main">
                {activeTab === 'analyses' && (
                  <>
                    <span className="record-icon"><ScanSearch size={17} /></span>
                    <div>
                      <Link className="history-title" to={`/analyses/${item.id}`}>{item.role || 'Untitled role'}</Link>
                      <small>{formatDate(item.created_at)}</small>
                    </div>
                  </>
                )}
                {activeTab === 'resumes' && (
                  <>
                    <span className="record-icon"><FileText size={17} /></span>
                    <div>
                      <b className="history-title">{item.filename}</b>
                      <small>{formatDate(item.created_at)} · extraction confidence {item.confidence}%</small>
                    </div>
                  </>
                )}
                {activeTab === 'jobs' && (
                  <>
                    <span className="record-icon"><BriefcaseBusiness size={17} /></span>
                    <div>
                      <b className="history-title">{item.title || 'Untitled role'}</b>
                      <small>{item.company || 'No company supplied'} · {formatDate(item.created_at)}</small>
                    </div>
                  </>
                )}
                {activeTab === 'interviews' && (
                  <>
                    <span className="record-icon"><MessageCircleQuestion size={17} /></span>
                    <div>
                      <b className="history-title">{item.role || 'Practice set'}</b>
                      <small>
                        {formatDate(item.created_at)} · {pluralise(item.question_count, 'question')}
                        {item.completed ? ' · completed' : ' · in progress'}
                      </small>
                    </div>
                  </>
                )}
              </div>
              <div className="history-actions">
                {activeTab === 'analyses' && (
                  <Link className="text-button" to={`/analyses/${item.id}`}>Open <ArrowRight size={15} /></Link>
                )}
                {activeTab === 'interviews' && (
                  <Link className="text-button" to="/interview">Continue <ArrowRight size={15} /></Link>
                )}
                <button
                  className="icon-link danger-link"
                  type="button"
                  aria-label="Delete item"
                  title="Delete item"
                  onClick={() => setPending({ tab: activeTab, item })}
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <ConfirmDialog
        open={Boolean(pending)}
        title="Delete this item?"
        description={description}
        confirmLabel="Delete"
        tone="danger"
        busy={deleting}
        onConfirm={confirmDelete}
        onCancel={() => setPending(null)}
      />
    </section>
  )
}
