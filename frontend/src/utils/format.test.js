import { describe, expect, it } from 'vitest'
import { formatDate, formatDateTime, initials, pluralise } from './format.js'

describe('initials', () => {
  it('uses the first letters of a full name', () => {
    expect(initials('Avery Chen')).toBe('AC')
  })

  it('falls back to the email local part', () => {
    expect(initials('', 'jordan.davis@example.com')).toBe('JD')
  })

  it('returns a safe default when nothing is supplied', () => {
    expect(initials('', '')).toBe('R')
  })
})

describe('pluralise', () => {
  it('handles singular and plural counts', () => {
    expect(pluralise(1, 'question')).toBe('1 question')
    expect(pluralise(2, 'question')).toBe('2 questions')
    expect(pluralise(2, 'analysis', 'analyses')).toBe('2 analyses')
  })
})

describe('date formatting', () => {
  it('formats a valid ISO date', () => {
    expect(formatDate('2026-01-15T10:30:00Z')).toMatch(/2026/)
  })

  it('returns a dash for invalid or missing values', () => {
    expect(formatDate('')).toBe('—')
    expect(formatDate('not-a-date')).toBe('—')
    expect(formatDateTime(null)).toBe('—')
  })
})
