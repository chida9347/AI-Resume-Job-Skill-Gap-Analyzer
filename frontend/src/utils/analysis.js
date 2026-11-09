export function normaliseInterviewQuestion(question = {}) {
  return {
    id: question.id || question.question || '',
    category: question.category || 'General',
    question: question.question || '',
    difficulty: question.difficulty || 'intermediate',
    relatedSkill: question.related_skill || question.relatedSkill || '',
    source: question.source || '',
    why: question.why || '',
    framework:
      question.answer_framework ||
      question.answerFramework ||
      question.example_answer ||
      'Use a concrete situation, explain your action and the trade-off, then state the result.',
    expectedConcepts: question.expected_concepts || question.expectedConcepts || [],
    project: question.project || '',
    technologies: question.technologies || [],
  }
}

export function interviewFromAnalysis(analysis) {
  const interview = analysis?.interview || {}
  const questions = (interview.questions || []).map(normaliseInterviewQuestion)
  return {
    role: interview.role || analysis?.job?.title || 'Your target role',
    questions,
    tips: interview.tips || [],
    categories: interview.categories || [...new Set(questions.map((item) => item.category))],
    disclaimer:
      interview.disclaimer ||
      'Questions are practice prompts generated from the role, skills and projects you supplied. They are not the questions an employer will ask.',
    method: interview.method || '',
  }
}

export function analysisCounts(analysis) {
  const comparison = analysis?.comparison || {}
  const matched = comparison.matched_skills || comparison.matched_required || []
  const missing = comparison.missing_skills || comparison.missing_required || []
  const partial = comparison.partial_required || comparison.partial_skills || []
  return {
    matched: matched.length,
    missing: missing.length,
    partial: partial.length,
    total: matched.length + missing.length,
    skillMatch: comparison.similarity_score ?? 0,
    atsScore: analysis?.ats?.ats_score ?? null,
  }
}

export function atsFeedbackAsSuggestions(ats) {
  if (!ats?.feedback?.length) return []
  return ats.feedback
    .filter((item) => !String(item).startsWith('Missing important keyword:'))
    .map((text, index) => ({
      id: `ats-feedback-${index}`,
      skill: 'ATS review',
      kind: 'review',
      text,
      rationale: 'Review this prompt and edit or remove anything that does not reflect your experience.',
    }))
}

export function selectedSuggestionGroups(suggestions, selectedIds) {
  const selected = suggestions.filter((item) => selectedIds.includes(item.id))
  return {
    skills: selected.filter((item) => item.kind === 'skill').map((item) => item.skill),
    reviewNotes: selected.filter((item) => item.kind !== 'skill').map((item) => item.text),
    selected,
  }
}
