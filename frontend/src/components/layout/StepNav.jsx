import React from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Check } from 'lucide-react'
import { useWorkspace } from '../../context/WorkspaceContext.jsx'

const steps = [
  { label: 'Analyze', path: '/analyze' },
  { label: 'Insights', path: '/results' },
  { label: 'Edit resume', path: '/editor' },
  { label: 'Interview prep', path: '/interview' },
]

export default function StepNav() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const { hasAnalysis } = useWorkspace()
  const activeStep = Math.max(
    0,
    steps.findIndex((step) => pathname === step.path || pathname.startsWith(`${step.path}/`)),
  )

  return (
    <nav className="step-nav" aria-label="Analysis progress">
      {steps.map((step, index) => (
        <button
          key={step.path}
          type="button"
          className={`step-item ${index === activeStep ? 'is-active' : ''} ${index < activeStep ? 'is-done' : ''}`}
          onClick={() => navigate(step.path)}
          disabled={index > 0 && !hasAnalysis}
          aria-current={index === activeStep ? 'step' : undefined}
        >
          <span className="step-number">{index < activeStep ? <Check size={13} /> : `0${index + 1}`}</span>
          <span>{step.label}</span>
        </button>
      ))}
    </nav>
  )
}
