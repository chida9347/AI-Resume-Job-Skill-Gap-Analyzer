import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Compass } from 'lucide-react'

export default function NotFoundPage() {
  return (
    <section className="notfound-page">
      <span className="notfound-code">404</span>
      <div className="eyebrow"><span className="eyebrow-line" /> PAGE NOT FOUND</div>
      <h1>This page is <span>elsewhere.</span></h1>
      <p>The link may be outdated, or the page may have moved. Your saved work is still in your workspace.</p>
      <div className="notfound-actions">
        <Link className="button-primary" to="/"><Compass size={16} /> Go home</Link>
        <Link className="button-secondary" to="/dashboard"><ArrowLeft size={15} /> Back to dashboard</Link>
      </div>
    </section>
  )
}
