import React, { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ArrowRight, LoaderCircle, LockKeyhole, Mail } from 'lucide-react'
import AuthLayout from '../components/layout/AuthLayout.jsx'
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
    <AuthLayout>
      <div className="auth-card-head">
        <span className="auth-kicker">WELCOME BACK</span>
        <h2>Sign in to your workspace</h2>
        <p>Your saved analyses, resumes and practice sets are waiting.</p>
      </div>

      <form className="auth-form" onSubmit={submit}>
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
              autoComplete="current-password"
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
              required
              placeholder="Your password"
            />
          </div>
        </label>

        {error && <p className="error-banner" role="alert">{error}</p>}

        <button className="button-primary auth-submit" type="submit" disabled={busy}>
          {busy ? <><LoaderCircle className="spin" size={16} /> Signing in...</> : <>Sign in <ArrowRight size={16} /></>}
        </button>
      </form>

      <p className="auth-switch">
        New to Roleprint? <Link to={`/register?next=${encodeURIComponent(next)}`}>Create an account</Link>
      </p>
    </AuthLayout>
  )
}
