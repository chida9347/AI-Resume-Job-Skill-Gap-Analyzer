import React, { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import {
  BriefcaseBusiness,
  History,
  LayoutDashboard,
  LogOut,
  Menu,
  ScanSearch,
  Settings,
  Target,
  UserRound,
  X,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext.jsx'
import { useWorkspace } from '../../context/WorkspaceContext.jsx'
import { initials } from '../../utils/format.js'

const links = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/analyze', label: 'Analyze', icon: ScanSearch },
  { to: '/jobs', label: 'Compare jobs', icon: BriefcaseBusiness },
]

export default function Topbar() {
  const { user, logout } = useAuth()
  const { hasAnalysis } = useWorkspace()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  async function handleLogout() {
    setOpen(false)
    await logout()
    navigate('/')
  }

  return (
    <header className="topbar">
      <Link className="wordmark" to="/" aria-label="Roleprint home" onClick={() => setOpen(false)}>
        <span className="brand-mark"><Target size={19} strokeWidth={2.4} /></span>
        <span>roleprint<span className="brand-period">.</span></span>
      </Link>

      <button
        className="topbar-menu"
        type="button"
        aria-expanded={open}
        aria-label={open ? 'Close navigation' : 'Open navigation'}
        onClick={() => setOpen((value) => !value)}
      >
        {open ? <X size={20} /> : <Menu size={20} />}
      </button>

      <nav className={`topnav ${open ? 'is-open' : ''}`} aria-label="Main navigation">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `topnav-link ${isActive ? 'is-active' : ''}`}
            onClick={() => setOpen(false)}
          >
            <Icon size={15} />
            <span>{label}</span>
          </NavLink>
        ))}
        {hasAnalysis && (
          <NavLink
            to="/results"
            className={({ isActive }) => `topnav-link ${isActive ? 'is-active' : ''}`}
            onClick={() => setOpen(false)}
          >
            <Target size={15} />
            <span>Current results</span>
          </NavLink>
        )}
        {user && (
          <NavLink
            to="/history"
            className={({ isActive }) => `topnav-link ${isActive ? 'is-active' : ''}`}
            onClick={() => setOpen(false)}
          >
            <History size={15} />
            <span>History</span>
          </NavLink>
        )}
      </nav>

      <div className="topbar-right">
        <span className="privacy-note"><span className="privacy-dot" /> Private by design</span>
        {user ? (
          <div className="user-menu">
            <Link className="user-chip" to="/profile" onClick={() => setOpen(false)}>
              <span className="user-avatar">{initials(user.full_name, user.email)}</span>
              <span className="user-chip-copy">
                <b>{user.full_name || 'Your account'}</b>
                <small>{user.email}</small>
              </span>
            </Link>
            <Link className="icon-link" to="/settings" aria-label="Settings" title="Settings" onClick={() => setOpen(false)}>
              <Settings size={16} />
            </Link>
            <button className="icon-link" type="button" onClick={handleLogout} aria-label="Sign out" title="Sign out">
              <LogOut size={16} />
            </button>
          </div>
        ) : (
          <div className="auth-links">
            <Link className="text-button" to="/login" onClick={() => setOpen(false)}>
              <UserRound size={15} /> Sign in
            </Link>
            <Link className="button-primary topbar-cta" to="/register" onClick={() => setOpen(false)}>
              Create account
            </Link>
          </div>
        )}
      </div>
    </header>
  )
}
