import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowDownToLine,
  CheckCircle2,
  KeyRound,
  LoaderCircle,
  ShieldAlert,
  Trash2,
} from 'lucide-react'
import ConfirmDialog from '../components/ui/ConfirmDialog.jsx'
import ErrorBanner from '../components/ui/ErrorBanner.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import * as api from '../services/api.js'
import { getErrorMessage } from '../utils/errors.js'
import { downloadJson } from '../utils/pdf.js'

export default function SettingsPage() {
  const { deleteAccount } = useAuth()
  const navigate = useNavigate()
  const [passwords, setPasswords] = useState({ current_password: '', new_password: '', confirm: '' })
  const [passwordBusy, setPasswordBusy] = useState(false)
  const [passwordError, setPasswordError] = useState('')
  const [passwordSaved, setPasswordSaved] = useState(false)

  const [exporting, setExporting] = useState(false)
  const [exportError, setExportError] = useState('')
  const [historyDialog, setHistoryDialog] = useState(false)
  const [historyBusy, setHistoryBusy] = useState(false)
  const [historyNote, setHistoryNote] = useState('')

  const [accountDialog, setAccountDialog] = useState(false)
  const [accountPassword, setAccountPassword] = useState('')
  const [accountBusy, setAccountBusy] = useState(false)
  const [accountError, setAccountError] = useState('')

  async function changePassword(event) {
    event.preventDefault()
    setPasswordError('')
    setPasswordSaved(false)
    if (passwords.new_password !== passwords.confirm) {
      setPasswordError('The new passwords do not match.')
      return
    }
    setPasswordBusy(true)
    try {
      await api.changePassword({
        current_password: passwords.current_password,
        new_password: passwords.new_password,
      })
      setPasswords({ current_password: '', new_password: '', confirm: '' })
      setPasswordSaved(true)
    } catch (failure) {
      setPasswordError(getErrorMessage(failure, 'Your password could not be changed.'))
    } finally {
      setPasswordBusy(false)
    }
  }

  async function exportHistory() {
    setExporting(true)
    setExportError('')
    try {
      const data = await api.exportHistory()
      downloadJson(data, `roleprint-history-${new Date().toISOString().slice(0, 10)}.json`)
    } catch (failure) {
      setExportError(getErrorMessage(failure, 'Your history could not be exported.'))
    } finally {
      setExporting(false)
    }
  }

  async function clearHistory() {
    setHistoryBusy(true)
    setHistoryNote('')
    try {
      await api.deleteHistory()
      setHistoryDialog(false)
      setHistoryNote('All saved resumes, roles, analyses and practice sets were deleted.')
    } catch (failure) {
      setHistoryNote(getErrorMessage(failure, 'Your history could not be cleared.'))
    } finally {
      setHistoryBusy(false)
    }
  }

  async function removeAccount() {
    if (!accountPassword.trim()) {
      setAccountError('Enter your password to confirm.')
      return
    }
    setAccountBusy(true)
    setAccountError('')
    try {
      await deleteAccount(accountPassword)
      setAccountDialog(false)
      navigate('/', { replace: true })
    } catch (failure) {
      setAccountError(getErrorMessage(failure, 'The account could not be deleted.'))
    } finally {
      setAccountBusy(false)
    }
  }

  return (
    <section className="settings-page">
      <div className="page-heading">
        <div className="eyebrow"><span className="eyebrow-line" /> ACCOUNT CONTROLS</div>
        <h1>Settings &amp; <span>privacy.</span></h1>
        <p>Change your password, export your data, clear saved history or delete your account.</p>
      </div>

      <div className="settings-grid">
        <form className="settings-card" onSubmit={changePassword}>
          <div className="panel-heading">
            <div><span className="panel-kicker">SECURITY</span><h2>Change password</h2></div>
            <KeyRound size={19} />
          </div>
          <label className="auth-field">
            <span>Current password</span>
            <input
              type="password"
              autoComplete="current-password"
              value={passwords.current_password}
              onChange={(event) => setPasswords({ ...passwords, current_password: event.target.value })}
              required
            />
          </label>
          <label className="auth-field">
            <span>New password</span>
            <input
              type="password"
              autoComplete="new-password"
              minLength={8}
              value={passwords.new_password}
              onChange={(event) => setPasswords({ ...passwords, new_password: event.target.value })}
              required
            />
          </label>
          <label className="auth-field">
            <span>Confirm new password</span>
            <input
              type="password"
              autoComplete="new-password"
              minLength={8}
              value={passwords.confirm}
              onChange={(event) => setPasswords({ ...passwords, confirm: event.target.value })}
              required
            />
          </label>
          {passwordError && <ErrorBanner>{passwordError}</ErrorBanner>}
          {passwordSaved && <p className="success-banner" role="status"><CheckCircle2 size={15} /> Password changed. Other sessions may need to sign in again.</p>}
          <button className="button-primary" type="submit" disabled={passwordBusy}>
            {passwordBusy ? <LoaderCircle className="spin" size={16} /> : <KeyRound size={16} />}
            {passwordBusy ? 'Updating…' : 'Update password'}
          </button>
        </form>

        <section className="settings-card">
          <div className="panel-heading">
            <div><span className="panel-kicker">YOUR DATA</span><h2>Export history</h2></div>
            <ArrowDownToLine size={19} />
          </div>
          <p>Download a JSON file containing the resumes, roles, analyses and practice sets you saved while signed in.</p>
          {exportError && <ErrorBanner>{exportError}</ErrorBanner>}
          <button className="button-secondary" type="button" onClick={exportHistory} disabled={exporting}>
            {exporting ? <LoaderCircle className="spin" size={16} /> : <ArrowDownToLine size={16} />}
            {exporting ? 'Preparing export…' : 'Download my data'}
          </button>
        </section>

        <section className="settings-card">
          <div className="panel-heading">
            <div><span className="panel-kicker">CLEAN UP</span><h2>Clear saved history</h2></div>
            <Trash2 size={19} />
          </div>
          <p>Delete every saved resume, job description, analysis and practice set. Your account remains active.</p>
          {historyNote && <p className="success-banner" role="status"><CheckCircle2 size={15} /> {historyNote}</p>}
          <button className="button-secondary danger-button" type="button" onClick={() => setHistoryDialog(true)}>
            <Trash2 size={16} /> Clear all history
          </button>
        </section>

        <section className="settings-card settings-danger">
          <div className="panel-heading">
            <div><span className="panel-kicker">DANGER ZONE</span><h2>Delete account</h2></div>
            <ShieldAlert size={19} />
          </div>
          <p>Permanently delete your account and every row tied to it. This cannot be undone.</p>
          <button className="button-primary button-danger" type="button" onClick={() => setAccountDialog(true)}>
            <Trash2 size={16} /> Delete my account
          </button>
        </section>
      </div>

      <ConfirmDialog
        open={historyDialog}
        title="Clear all saved history?"
        description="Every saved resume, role, analysis and practice set will be deleted. Your account stays active. This cannot be undone."
        confirmLabel="Clear history"
        tone="danger"
        busy={historyBusy}
        onConfirm={clearHistory}
        onCancel={() => setHistoryDialog(false)}
      />

      {accountDialog && (
        <div className="modal-backdrop" role="presentation">
          <div className="modal-card" role="dialog" aria-modal="true" aria-labelledby="delete-account-title">
            <h2 id="delete-account-title">Delete your account?</h2>
            <p>This permanently removes your profile and all saved data. Enter your password to confirm.</p>
            <label className="auth-field">
              <span>Password</span>
              <input
                type="password"
                autoComplete="current-password"
                value={accountPassword}
                onChange={(event) => setAccountPassword(event.target.value)}
                autoFocus
              />
            </label>
            {accountError && <ErrorBanner>{accountError}</ErrorBanner>}
            <div className="modal-actions">
              <button className="button-secondary" type="button" onClick={() => setAccountDialog(false)} disabled={accountBusy}>
                Cancel
              </button>
              <button className="button-primary button-danger" type="button" onClick={removeAccount} disabled={accountBusy}>
                {accountBusy ? <LoaderCircle className="spin" size={15} /> : <Trash2 size={15} />}
                {accountBusy ? 'Deleting…' : 'Delete account'}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
