import React from 'react'
import { AlertCircle } from 'lucide-react'

export default function ErrorBanner({ children, className = '' }) {
  if (!children) return null
  return (
    <p className={`error-banner ${className}`} role="alert">
      <AlertCircle size={15} />
      <span>{children}</span>
    </p>
  )
}
