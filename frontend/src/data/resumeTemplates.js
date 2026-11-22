export const RESUME_TEMPLATES = [
  {
    id: 'classic',
    name: 'Classic ATS',
    tagline: 'The trusted single-column layout every parser reads cleanly.',
    description: 'Standard sections in a safe order with plain headings. Best starting point for any role.',
    recommended: true,
    sections: [
      { id: 'summary', label: 'Professional Summary' },
      { id: 'skills', label: 'Skills' },
      { id: 'experience', label: 'Experience' },
      { id: 'education', label: 'Education' },
      { id: 'certifications', label: 'Certifications' },
    ],
  },
  {
    id: 'modern',
    name: 'Modern Minimal',
    tagline: 'Experience-first single column with a lighter skills section.',
    description: 'Prioritises a strong experience block, then skills and education. Clean and dense.',
    sections: [
      { id: 'summary', label: 'Professional Summary' },
      { id: 'experience', label: 'Experience' },
      { id: 'skills', label: 'Skills' },
      { id: 'education', label: 'Education' },
      { id: 'certifications', label: 'Certifications' },
    ],
  },
  {
    id: 'executive',
    name: 'Executive One-Page',
    tagline: 'Achievement-led single column for senior and leadership roles.',
    description: 'Keeps experience and certifications close to the top, then skills. Built for one-page CVs.',
    sections: [
      { id: 'summary', label: 'Professional Summary' },
      { id: 'experience', label: 'Experience' },
      { id: 'education', label: 'Education' },
      { id: 'certifications', label: 'Certifications' },
      { id: 'skills', label: 'Skills' },
    ],
  },
]

export function getResumeTemplate(templateId) {
  return RESUME_TEMPLATES.find((template) => template.id === templateId) || RESUME_TEMPLATES[0]
}

export function createBuilderState() {
  return {
    name: '',
    title: '',
    summary: '',
    skills: '',
    experience: [
      { id: 1, role: '', company: '', startDate: '', endDate: '', points: [''] },
    ],
    education: [
      { id: 1, school: '', degree: '', year: '' },
    ],
    certifications: '',
  }
}

const SECTION_TITLES = {
  summary: 'Professional Summary',
  skills: 'Skills',
  experience: 'Experience',
  education: 'Education',
  certifications: 'Certifications',
}

function splitList(value) {
  return String(value || '')
    .split(/[,;\n]/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function pushSection(sections, id, heading, lines) {
  const clean = (lines || []).map((line) => String(line ?? '').trim()).filter(Boolean)
  if (!clean.length) return
  sections.push({ id, heading, lines: clean })
}

export function buildResumeSections(state, template) {
  const sections = []
  const templateSections = template?.sections?.length ? template.sections : RESUME_TEMPLATES[0].sections
  const includes = (id) => templateSections.some((section) => section.id === id)

  if ((state.name || '').trim()) {
    pushSection(sections, 'header', '', [(state.name || '').trim(), (state.title || '').trim()].filter(Boolean))
  }

  if (includes('summary') && (state.summary || '').trim()) {
    pushSection(sections, 'summary', SECTION_TITLES.summary, [(state.summary || '').trim()])
  }

  const skills = splitList(state.skills)
  if (includes('skills') && skills.length) {
    pushSection(sections, 'skills', SECTION_TITLES.skills, skills.map((skill) => `- ${skill}`))
  }

  for (const entry of state.experience || []) {
    const lines = []
    const when = [entry.startDate, entry.endDate].filter(Boolean).join(' - ')
    const heading = [entry.role, entry.company, when].filter(Boolean).map((value) => String(value).trim()).filter(Boolean).join(', ')
    if (heading) lines.push(heading)
    const points = (entry.points || []).flatMap((point) => String(point || '').split(/\r?\n/))
    for (const point of points) {
      const text = point.trim()
      if (text) lines.push(`- ${text}`)
    }
    if (lines.length) pushSection(sections, `experience-${entry.id}`, SECTION_TITLES.experience, lines)
  }

  for (const entry of state.education || []) {
    const bits = [
      entry.degree,
      entry.school,
      entry.year ? `(${entry.year})` : null,
    ].filter(Boolean).map((value) => String(value).trim()).filter(Boolean)
    if (bits.length) {
      pushSection(sections, `education-${entry.id}`, SECTION_TITLES.education, [bits.join(', ')])
    }
  }

  const certifications = splitList(state.certifications)
  if (includes('certifications') && certifications.length) {
    pushSection(sections, 'certifications', SECTION_TITLES.certifications, certifications.map((cert) => `- ${cert}`))
  }

  return sections
}

export function buildResumeText(state, template) {
  return buildResumeSections(state, template)
    .map((section) => (section.heading ? `${section.heading}\n${section.lines.join('\n')}` : section.lines.join('\n')))
    .map((chunk) => chunk.replace(/^\n+|\n+$/g, ''))
    .filter((chunk) => chunk.length > 0)
    .join('\n\n')
}
