import React, { useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Topbar from './Topbar.jsx'
import StepNav from './StepNav.jsx'

const analysisRoutes = ['/analyze', '/results', '/editor', '/interview']

export default function AppLayout() {
  const { pathname } = useLocation()
  const showSteps = analysisRoutes.some((route) => pathname === route || pathname.startsWith(`${route}/`))

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])

  return (
    <div className="app-shell">
      <Topbar />
      {showSteps && <StepNav />}
      <main className={`main-content ${pathname === '/' ? 'main-home' : ''}`}>
        <Outlet />
      </main>
      <footer className="site-footer">
        <span>ROLEPRINT <i>·</i> CAREER TOOLS, WITH CLARITY</span>
        <span>Useful guidance. Your decisions.</span>
      </footer>
    </div>
  )
}
