import React from 'react'
import { LoaderCircle } from 'lucide-react'

export default function PageLoader({ label = 'Loading…' }) {
  return (
    <div className="page-loader" role="status" aria-live="polite">
      <LoaderCircle className="spin" size={22} />
      <span>{label}</span>
    </div>
  )
}
