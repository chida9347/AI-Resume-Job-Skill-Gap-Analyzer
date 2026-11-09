import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import SkillsSnapshot from './SkillsSnapshot.jsx'

describe('SkillsSnapshot', () => {
  it('renders matched, partial and missing skills with honest labels', () => {
    render(
      <SkillsSnapshot
        comparison={{
          matched_skills: ['python', 'sql'],
          missing_skills: ['airflow'],
          partial_required: ['pandas'],
          matched_preferred: ['docker'],
          missing_preferred: ['kubernetes'],
          skill_labels: { python: 'Python', sql: 'SQL', airflow: 'Airflow', pandas: 'pandas' },
        }}
      />,
    )

    expect(screen.getByText('Python')).toBeInTheDocument()
    expect(screen.getByText('Airflow')).toBeInTheDocument()
    expect(screen.getByText('Related, not explicit')).toBeInTheDocument()
    expect(screen.getByText(/not counted as an explicit match/i)).toBeInTheDocument()
    expect(screen.getByText(/cannot tell whether you have an unlisted skill/i)).toBeInTheDocument()
  })

  it('shows an empty note when every requested skill is found', () => {
    render(<SkillsSnapshot comparison={{ matched_skills: ['python'], missing_skills: [] }} />)

    expect(screen.getByText(/All detected job skills appear/i)).toBeInTheDocument()
  })
})
