import React, { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ArrowRight, LoaderCircle, LockKeyhole, Mail, ShieldCheck, UserRound } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'
import { getErrorMessage } from '../utils/errors.js'

export default function RegisterPage() {
  const { user, register } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const params = new URLSearchParams(location.search)
  const next = params.get('next') || '/dashboard'
  const [form, setForm] = useState({ full_name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to={next} replace />

  async function submit(event) {
    event.preventDefault()
    if (form.password.length < 8) {
      setError('Choose a password with at least 8 characters.')
      return
    }
    setBusy(true)
    setError('')
    try {
      await register(form)
      navigate(next, { replace: true })
    } catch (failure) {
      setError(getErrorMessage(failure, 'Account creation failed. Try a different email address.'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="auth-page">
      <div className="auth-card">
        <div className="eyebrow"><span className="eyebrow-line" /> CREATE YOUR ACCOUNT</div>
        <h1>Save your <span>progress.</span></h1>
        <p className="auth-lede">Keep resumes, analyses and interview practice in one private workspace.</p>
        <form className="auth-form" onSubmit={submit}>
          <label className="auth-field">
            <span><UserRound size={14} /> Full name <small>OPTIONAL</small></span>
            <input
              type="text"
              autoComplete="name"
              value={form.full_name}
              onChange={(event) => setForm({ ...form, full_name: event.target.value })}
              placeholder="Avery Chen"
            />
          </label>
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
              autoComplete="new-password"
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
              required
              minLength={8}
              placeholder="At least 8 characters"
            />
          </label>
          {error && <p className="error-banner" role="alert">{error}</p>}
          <button className="button-primary auth-submit" type="submit" disabled={busy}>
            {busy ? <><LoaderCircle className="spin" size={16} /> Creating account…</> : <>Create account <ArrowRight size={16} /></>}
          </button>
        </form>
        <p className="auth-switch">Already have an account? <Link to={`/login?next=${encodeURIComponent(next)}`}>Sign in</Link></p>
        <p className="auth-note"><ShieldCheck size={14} /> You can export or permanently delete your data from Settings.</p>
      </div>
      <aside className="auth-aside auth-aside-register">
        <div className="eyebrow"><span className="eyebrow-line" /> BUILT FOR HONESTY</div>
        <h2>No invented<br /><span>experience.</span></h2>
        <ul>
          <li>Placeholders are explicit and editable</li>
          <li>Semantic similarity is never counted as proof</li>
          <li>ATS scores are capped and explained</li>
          <li>AI rewriting requires explicit consent</li>
        </ul>
        <p>The platform works without OpenAI keys, OCR or model downloads. Optional features are opt-in.</p>
      </aside>
    </section>
  )
}
