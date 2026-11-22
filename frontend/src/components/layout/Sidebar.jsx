import React from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import {
  BookOpenCheck,
  BriefcaseBusiness,
  History,
  LayoutDashboard,
  LayoutTemplate,
  LogOut,
  MessageCircleQuestion,
  ScanSearch,
  Settings,
  Target,
  UserRound,
  X,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext.jsx'
import { useWorkspace } from '../../context/WorkspaceContext.jsx'
import { initials } from '../../utils/format.js'

const groups = [
  {
    label: 'Workspace',
    links: [
      { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
      { to: '/analyze', label: 'New analysis', icon: ScanSearch },
      { to: '/history', label: 'History', icon: History },
    ],
  },
  {
    label: 'Career tools',
    links: [
      { to: '/jobs', label: 'Compare roles', icon: BriefcaseBusiness },
      { to: '/interview', label: 'Interview prep', icon: MessageCircleQuestion },
      { to: '/roadmap', label: 'Learning roadmap', icon: BookOpenCheck },
      { to: '/builder', label: 'Resume builder', icon: LayoutTemplate },
    ],
  },
  {
    label: 'Account',
    links: [
      { to: '/profile', label: 'Profile', icon: UserRound },
      { to: '/settings', label: 'Settings', icon: Settings },
    ],
  },
]

export default function Sidebar({ open, onClose }) {
  const { user, logout } = useAuth()
  const { hasAnalysis } = useWorkspace()
  const navigate = useNavigate()

  async function handleLogout() {
    onClose?.()
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <>
      <div className={`shell-scrim ${open ? 'is-visible' : ''}`} onClick={onClose} aria-hidden="true" />
      <aside id="workspace-sidebar" className={`shell-sidebar ${open ? 'is-open' : ''}`} aria-label="Workspace navigation">
        <div className="sidebar-top">
          <Link className="sidebar-brand" to="/dashboard" onClick={onClose}>
            <span className="sidebar-brand-mark"><Target size={20} strokeWidth={2.4} /></span>
            <span className="sidebar-wordmark">roleprint<span>.</span></span>
          </Link>
          <button className="sidebar-close" type="button" onClick={onClose} aria-label="Close navigation">
            <X size={19} />
          </button>
        </div>

        <nav className="sidebar-nav">
          {groups.map((group) => (
            <div className="sidebar-group" key={group.label}>
              <span className="sidebar-group-label">{group.label}</span>
              {group.links.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  onClick={onClose}
                  className={({ isActive }) => `sidebar-link ${isActive ? 'is-active' : ''}`}
                >
                  <Icon size={17} />
                  <span>{label}</span>
                </NavLink>
              ))}
              {group.label === 'Workspace' && hasAnalysis && (
                <NavLink
                  to="/results"
                  onClick={onClose}
                  className={({ isActive }) => `sidebar-link ${isActive ? 'is-active' : ''}`}
                >
                  <Target size={17} />
                  <span>Current results</span>
                  <span className="sidebar-live-dot" aria-hidden="true" />
                </NavLink>
              )}
            </div>
          ))}
        </nav>

        <div className="sidebar-footer">
          <Link className="sidebar-user" to="/profile" onClick={onClose}>
            <span className="sidebar-avatar">{initials(user?.full_name, user?.email)}</span>
            <span className="sidebar-user-copy">
              <b>{user?.full_name || 'Your account'}</b>
              <small>{user?.email}</small>
            </span>
          </Link>
          <button className="sidebar-logout" type="button" onClick={handleLogout}>
            <LogOut size={16} />
            <span>Sign out</span>
          </button>
        </div>
      </aside>
    </>
  )
}
