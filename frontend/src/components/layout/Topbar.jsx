import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Menu, ShieldCheck, Target } from 'lucide-react'
import { useWorkspace } from '../../context/WorkspaceContext.jsx'
import { useAuth } from '../../context/AuthContext.jsx'
import { initials } from '../../utils/format.js'

const titles = {
  '/dashboard': { kicker: 'Workspace', title: 'Dashboard' },
  '/analyze': { kicker: 'New analysis', title: 'Analyze a resume' },
  '/results': { kicker: 'Analysis', title: 'Results' },
  '/editor': { kicker: 'Draft', title: 'Resume editor' },
  '/roadmap': { kicker: 'Career tools', title: 'Learning roadmap' },
  '/interview': { kicker: 'Career tools', title: 'Interview prep' },
  '/jobs': { kicker: 'Career tools', title: 'Compare roles' },
  '/history': { kicker: 'Workspace', title: 'History' },
  '/profile': { kicker: 'Account', title: 'Profile' },
  '/settings': { kicker: 'Account', title: 'Settings' },
}

function titleFor(pathname) {
  if (titles[pathname]) return titles[pathname]
  if (pathname.startsWith('/analyses/')) return { kicker: 'Saved analysis', title: 'Snapshot' }
  return { kicker: 'Roleprint', title: 'Workspace' }
}

export default function Topbar({ onMenu, navOpen = false }) {
  const { pathname } = useLocation()
  const { hasAnalysis } = useWorkspace()
  const { user } = useAuth()
  const meta = titleFor(pathname)

  return (
    <header className="shell-topbar">
      <button
        className="topbar-burger"
        type="button"
        onClick={onMenu}
        aria-label="Open navigation"
        aria-expanded={navOpen}
        aria-controls="workspace-sidebar"
      >
        <Menu size={20} />
      </button>

      <div className="topbar-heading">
        <span>{meta.kicker}</span>
        <h1>{meta.title}</h1>
      </div>

      <div className="topbar-actions">
        {hasAnalysis && pathname !== '/results' && (
          <Link className="topbar-pill" to="/results">
            <Target size={14} />
            Current results
          </Link>
        )}
        <span className="topbar-privacy"><ShieldCheck size={14} /> Private workspace</span>
        <Link className="topbar-avatar" to="/profile" aria-label="Open profile">
          {initials(user?.full_name, user?.email)}
        </Link>
      </div>
    </header>
  )
}
