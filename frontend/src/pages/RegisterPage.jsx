import React, { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ArrowRight, LoaderCircle, LockKeyhole, Mail, UserRound } from 'lucide-react'
import AuthLayout from '../components/layout/AuthLayout.jsx'
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
    <AuthLayout>
      <div className="auth-card-head">
        <span className="auth-kicker">CREATE YOUR WORKSPACE</span>
        <h2>Start your private workspace</h2>
        <p>Keep resumes, analyses and practice sets together. You control your data.</p>
      </div>

      <form className="auth-form" onSubmit={submit}>
        <label className="auth-field">
          <span>Full name <small>OPTIONAL</small></span>
          <div className="auth-input">
            <UserRound size={16} />
            <input
              type="text"
              autoComplete="name"
              value={form.full_name}
              onChange={(event) => setForm({ ...form, full_name: event.target.value })}
              placeholder="Avery Chen"
            />
          </div>
        </label>
        <label className="auth-field">
          <span>Email</span>
          <div className="auth-input">
            <Mail size={16} />
            <input
              type="email"
              autoComplete="email"
              value={form.email}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
              required
              placeholder="you@example.com"
            />
          </div>
        </label>
        <label className="auth-field">
          <span>Password</span>
          <div className="auth-input">
            <LockKeyhole size={16} />
            <input
              type="password"
              autoComplete="new-password"
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
              required
              minLength={8}
              placeholder="At least 8 characters"
            />
          </div>
        </label>

        {error && <p className="error-banner" role="alert">{error}</p>}

        <button className="button-primary auth-submit" type="submit" disabled={busy}>
          {busy ? <><LoaderCircle className="spin" size={16} /> Creating account...</> : <>Create account <ArrowRight size={16} /></>}
        </button>
      </form>

      <p className="auth-switch">
        Already have an account? <Link to={`/login?next=${encodeURIComponent(next)}`}>Sign in</Link>
      </p>
      <p className="auth-note">
        By creating an account you agree that analyses are estimates, not guarantees. You can export or
        permanently delete your data from Settings.
      </p>
    </AuthLayout>
  )
}
