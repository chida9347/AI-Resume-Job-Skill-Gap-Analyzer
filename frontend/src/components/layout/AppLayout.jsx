import React, { useEffect, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar.jsx'
import StepNav from './StepNav.jsx'
import Topbar from './Topbar.jsx'

const analysisRoutes = ['/analyze', '/results', '/editor', '/interview']

export default function AppLayout() {
  const { pathname } = useLocation()
  const [navOpen, setNavOpen] = useState(false)
  const showSteps = analysisRoutes.some((route) => pathname === route || pathname.startsWith(`${route}/`))

  useEffect(() => {
    window.scrollTo(0, 0)
    setNavOpen(false)
  }, [pathname])

  useEffect(() => {
    if (!navOpen) return undefined
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') setNavOpen(false)
    }
    window.addEventListener('keydown', closeOnEscape)
    return () => {
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', closeOnEscape)
    }
  }, [navOpen])

  return (
    <div className="shell">
      <Sidebar open={navOpen} onClose={() => setNavOpen(false)} />
      <div className="shell-body">
        <Topbar onMenu={() => setNavOpen(true)} navOpen={navOpen} />
        {showSteps && <StepNav />}
        <main className="shell-content">
          <Outlet />
        </main>
        <footer className="shell-footer">
          <span>ROLEPRINT <i>&middot;</i> CAREER TOOLS, WITH CLARITY</span>
          <span>Useful guidance. Your decisions.</span>
        </footer>
      </div>
    </div>
  )
}
