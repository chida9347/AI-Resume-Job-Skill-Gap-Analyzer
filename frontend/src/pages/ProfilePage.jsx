import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, CheckCircle2, LoaderCircle, Mail, Settings, ShieldCheck, UserRound } from 'lucide-react'
import ErrorBanner from '../components/ui/ErrorBanner.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { getErrorMessage } from '../utils/errors.js'
import { formatDate, initials } from '../utils/format.js'

export default function ProfilePage() {
  const { user, updateProfile } = useAuth()
  const [form, setForm] = useState({ full_name: user?.full_name || '', headline: user?.headline || '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setSaved(false)
    try {
      await updateProfile({ full_name: form.full_name, headline: form.headline })
      setSaved(true)
    } catch (failure) {
      setError(getErrorMessage(failure, 'Your profile could not be updated.'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="profile-page">
      <div className="page-heading">
        <div className="eyebrow"><span className="eyebrow-line" /> YOUR ACCOUNT</div>
        <h1>Profile <span>details.</span></h1>
        <p>Your name and headline appear in your workspace. They are not included in saved analyses.</p>
      </div>

      <div className="profile-grid">
        <section className="profile-card">
          <div className="profile-identity">
            <span className="profile-avatar">{initials(user?.full_name, user?.email)}</span>
            <div>
              <b>{user?.full_name || 'Your account'}</b>
              <span>{user?.headline || 'Add a headline to describe your focus.'}</span>
            </div>
          </div>
          <div className="profile-meta">
            <div><Mail size={15} /><span>{user?.email}</span></div>
            <div><ShieldCheck size={15} /><span>Member since {formatDate(user?.created_at)}</span></div>
          </div>
          <Link className="button-secondary" to="/settings"><Settings size={15} /> Account settings <ArrowRight size={15} /></Link>
        </section>

        <form className="profile-card" onSubmit={submit}>
          <div className="panel-heading">
            <div><span className="panel-kicker">EDIT PROFILE</span><h2>How should we address you?</h2></div>
            <UserRound size={19} />
          </div>
          <label className="auth-field">
            <span>Full name</span>
            <input
              type="text"
              value={form.full_name}
              onChange={(event) => setForm({ ...form, full_name: event.target.value })}
              maxLength={160}
              placeholder="Avery Chen"
            />
          </label>
          <label className="auth-field">
            <span>Headline <small>OPTIONAL</small></span>
            <input
              type="text"
              value={form.headline}
              onChange={(event) => setForm({ ...form, headline: event.target.value })}
              maxLength={200}
              placeholder="e.g. Backend engineer moving into platform work"
            />
          </label>
          {error && <ErrorBanner>{error}</ErrorBanner>}
          {saved && <p className="success-banner" role="status"><CheckCircle2 size={15} /> Profile updated.</p>}
          <button className="button-primary" type="submit" disabled={busy}>
            {busy ? <LoaderCircle className="spin" size={16} /> : <CheckCircle2 size={16} />}
            {busy ? 'Saving…' : 'Save profile'}
          </button>
        </form>
      </div>
    </section>
  )
}
