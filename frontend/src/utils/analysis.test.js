import { describe, expect, it } from 'vitest'
import {
  analysisCounts,
  atsFeedbackAsSuggestions,
  interviewFromAnalysis,
  normaliseInterviewQuestion,
  selectedSuggestionGroups,
} from './analysis.js'

describe('normaliseInterviewQuestion', () => {
  it('normalises the new answer_framework shape', () => {
    const question = normaliseInterviewQuestion({
      id: 'q1',
      category: 'Backend',
      question: 'How do you design an API?',
      difficulty: 'senior',
      related_skill: 'FastAPI',
      why: 'Tests API design.',
      answer_framework: 'Describe the contract, then trade-offs.',
      expected_concepts: ['REST', 'versioning'],
    })

    expect(question.relatedSkill).toBe('FastAPI')
    expect(question.framework).toContain('contract')
    expect(question.expectedConcepts).toEqual(['REST', 'versioning'])
  })

  it('falls back to the legacy example_answer field', () => {
    const question = normaliseInterviewQuestion({
      question: 'Tell me about a project.',
      example_answer: 'Use STAR.',
    })

    expect(question.framework).toBe('Use STAR.')
    expect(question.category).toBe('General')
  })
})

describe('interviewFromAnalysis', () => {
  it('returns safe defaults when an analysis has no interview block', () => {
    const result = interviewFromAnalysis({ job: { title: 'Data Analyst' } })

    expect(result.role).toBe('Data Analyst')
    expect(result.questions).toEqual([])
    expect(result.disclaimer).toContain('practice prompts')
  })
})

describe('analysisCounts', () => {
  it('counts required matches, gaps and partial skills', () => {
    const counts = analysisCounts({
      comparison: {
        matched_required: ['python', 'sql'],
        missing_required: ['airflow'],
        partial_required: ['pandas'],
        similarity_score: 67,
      },
      ats: { ats_score: 71 },
    })

    expect(counts).toEqual({ matched: 2, missing: 1, partial: 1, total: 3, skillMatch: 67, atsScore: 71 })
  })

  it('supports the legacy matched_skills keys', () => {
    const counts = analysisCounts({
      comparison: { matched_skills: ['python'], missing_skills: ['sql'], similarity_score: 50 },
    })

    expect(counts.matched).toBe(1)
    expect(counts.missing).toBe(1)
    expect(counts.atsScore).toBeNull()
  })
})

describe('atsFeedbackAsSuggestions', () => {
  it('drops keyword lines and keeps review prompts', () => {
    const suggestions = atsFeedbackAsSuggestions({
      feedback: [
        'Missing important keyword: Kubernetes',
        'Add a measurable result to your most recent role.',
      ],
    })

    expect(suggestions).toHaveLength(1)
    expect(suggestions[0].kind).toBe('review')
    expect(suggestions[0].text).toContain('measurable result')
  })
})

describe('selectedSuggestionGroups', () => {
  it('separates confirmed skills from review notes', () => {
    const suggestions = [
      { id: 'a', kind: 'skill', skill: 'Python' },
      { id: 'b', kind: 'review', text: 'Add a metric.' },
      { id: 'c', kind: 'skill', skill: 'SQL' },
    ]

    const groups = selectedSuggestionGroups(suggestions, ['a', 'b'])

    expect(groups.skills).toEqual(['Python'])
    expect(groups.reviewNotes).toEqual(['Add a metric.'])
    expect(groups.selected).toHaveLength(2)
  })
})
