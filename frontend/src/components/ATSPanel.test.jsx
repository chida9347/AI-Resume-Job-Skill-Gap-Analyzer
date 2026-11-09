import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import ATSPanel from './ATSPanel.jsx'

const result = {
  ats_score: 72,
  keyword_match: 64,
  confidence: 80,
  section_score: { skills: 80, experience: 70 },
  breakdown: [
    { component: 'required_skill_coverage', label: 'Required skill coverage', explanation: 'Two of three required skills found.', points: 20, max_points: 30 },
  ],
  score_caps: [{ reason: 'Required skills are missing.', max: 79 }],
  missing_keywords: ['airflow'],
  feedback: ['Missing important keyword: airflow', 'Add a measurable result.'],
  disclaimer: 'This is an estimate, not an employer ATS score.',
}

describe('ATSPanel', () => {
  it('renders an estimate with caps and the disclaimer', () => {
    render(<ATSPanel result={result} loading={false} error="" />)

    expect(screen.getByRole('img', { name: /ATS simulation score 72/i })).toBeInTheDocument()
    expect(screen.getByText(/Why this is not a perfect score/i)).toBeInTheDocument()
    expect(screen.getByText(/Required skills are missing. Maximum 79./i)).toBeInTheDocument()
    expect(screen.getByText(/not an employer ATS score/i)).toBeInTheDocument()
    expect(screen.getByText(/Job word not found in resume: airflow/i)).toBeInTheDocument()
  })

  it('renders a loading state instead of stale scores', () => {
    render(<ATSPanel result={result} loading error="" />)

    expect(screen.getByText(/Checking resume wording/i)).toBeInTheDocument()
    expect(screen.queryByRole('img')).not.toBeInTheDocument()
  })

  it('renders an error state', () => {
    render(<ATSPanel result={null} loading={false} error="Could not score." />)

    expect(screen.getByRole('alert')).toHaveTextContent('Could not score.')
  })
})
