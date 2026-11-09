import React, { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ArrowRight, LoaderCircle, LockKeyhole, Mail, ShieldCheck } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'
import { getErrorMessage } from '../utils/errors.js'

export default function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const params = new URLSearchParams(location.search)
  const next = params.get('next') || '/dashboard'
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to={next} replace />

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      await login(form)
      navigate(next, { replace: true })
    } catch (failure) {
      setError(getErrorMessage(failure, 'Sign-in failed. Check your email and password.'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="auth-page">
      <div className="auth-card">
        <div className="eyebrow"><span className="eyebrow-line" /> WELCOME BACK</div>
        <h1>Sign in to your <span>workspace.</span></h1>
        <p className="auth-lede">Your saved analyses, resumes and interview practice stay tied to your account.</p>
        <form className="auth-form" onSubmit={submit}>
          <label className="auth-field">
            <span><Mail size={14} /> Email</span>
            <input
              type="email"
              autoComplete="email"
              value={form.email}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
              required
              placeholder="you@example.com"
            />
          </label>
          <label className="auth-field">
            <span><LockKeyhole size={14} /> Password</span>
            <input
              type="password"
              autoComplete="current-password"
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
              required
              placeholder="Your password"
            />
          </label>
          {error && <p className="error-banner" role="alert">{error}</p>}
          <button className="button-primary auth-submit" type="submit" disabled={busy}>
            {busy ? <><LoaderCircle className="spin" size={16} /> Signing in…</> : <>Sign in <ArrowRight size={16} /></>}
          </button>
        </form>
        <p className="auth-switch">New to Roleprint? <Link to={`/register?next=${encodeURIComponent(next)}`}>Create an account</Link></p>
        <p className="auth-note"><ShieldCheck size={14} /> Anonymous analysis is always available without an account.</p>
      </div>
      <aside className="auth-aside">
        <div className="eyebrow"><span className="eyebrow-line" /> WHAT YOU GET</div>
        <h2>Keep the work<br /><span>you have done.</span></h2>
        <ul>
          <li>Saved resume and job snapshots</li>
          <li>Reopen previous alignment reports</li>
          <li>Interview practice attempts and feedback</li>
          <li>Export or delete your history at any time</li>
        </ul>
        <p>Passwords are hashed with bcrypt. Access tokens are short-lived and refresh tokens are rotated on use.</p>
      </aside>
    </section>
  )
}
