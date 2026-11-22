import { describe, expect, it } from 'vitest'
import { RESUME_TEMPLATES, buildResumeSections, buildResumeText, createBuilderState, getResumeTemplate } from './resumeTemplates.js'

describe('resumeTemplates', () => {
  it('exposes a list of ATS-friendly templates', () => {
    expect(RESUME_TEMPLATES.length).toBeGreaterThanOrEqual(3)
    expect(RESUME_TEMPLATES[0].id).toBe('classic')
    for (const template of RESUME_TEMPLATES) {
      expect(template.sections.length).toBeGreaterThan(0)
      for (const section of template.sections) {
        expect(section.id).toBeTruthy()
        expect(section.label).toBeTruthy()
      }
    }
  })

  it('returns the requested template', () => {
    expect(getResumeTemplate('modern').id).toBe('modern')
    expect(getResumeTemplate('missing')).toBe(getResumeTemplate('classic'))
  })

  it('creates a blank builder state with one empty experience and education entry', () => {
    const state = createBuilderState()
    expect(state.name).toBe('')
    expect(state.title).toBe('')
    expect(state.skills).toBe('')
    expect(state.experience).toHaveLength(1)
    expect(state.education).toHaveLength(1)
  })

  it('builds resume text with the header and included sections in template order', () => {
    const template = getResumeTemplate('classic')
    const text = buildResumeText(
      {
        name: 'Avery Chen',
        title: 'Senior Data Analyst',
        summary: 'Data analyst with real experience.',
        skills: 'SQL, Python',
        experience: [
          {
            id: 1,
            role: 'Senior Data Analyst',
            company: 'Northwind Retail',
            startDate: '2021',
            endDate: '2024',
            points: ['Built dashboards', 'Automated reports'],
          },
        ],
        education: [{ id: 1, school: 'State University', degree: 'BSc Economics', year: '2018' }],
        certifications: 'AWS Solutions Architect',
      },
      template,
    )

    expect(text).toContain('Avery Chen')
    expect(text).toContain('Senior Data Analyst')
    expect(text).toContain('Professional Summary')
    expect(text).toContain('Skills')
    expect(text).toContain('- SQL')
    expect(text).toContain('- Python')
    expect(text).toContain('Experience')
    expect(text).toContain('Education')
    expect(text).toContain('Certifications')
    expect(text).toContain('AWS Solutions Architect')
    expect(text).not.toContain('Missing Section')
  })

  it('skips empty sections and only includes sections from the template', () => {
    const sections = buildResumeSections(
      { name: 'Avery Chen', title: '', summary: '', skills: '', experience: [], education: [], certifications: '' },
      getResumeTemplate('modern'),
    )
    expect(sections.map((section) => section.id)).toEqual(['header'])
  })

  it('formats experience with dates and bullets', () => {
    const sections = buildResumeSections(
      {
        name: 'Avery Chen',
        title: '',
        summary: '',
        skills: '',
        experience: [{ id: 7, role: 'Data Analyst', company: 'Northwind Retail', startDate: '2021', endDate: '2024', points: ['Built dashboards', 'Automated reports'] }],
        education: [],
        certifications: '',
      },
      getResumeTemplate('classic'),
    )
    const experience = sections.find((section) => section.id === 'experience-7')
    expect(experience).toBeTruthy()
    expect(experience.heading).toBe('Experience')
    expect(experience.lines[0]).toContain('Data Analyst')
    expect(experience.lines[1]).toBe('- Built dashboards')
    expect(experience.lines[2]).toBe('- Automated reports')
  })
})
