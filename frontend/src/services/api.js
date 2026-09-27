import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 120000,
})

export async function analyzeResume(file, jobDescription) {
  const form = new FormData()
  form.append('file', file)
  const resume = await api.post('/upload_resume', form)
  const job = await api.post('/analyze_job', { text: jobDescription })
  const comparison = await api.post('/compare', {
    resume_skills: resume.data.skills,
    job_skills: job.data.required_skills,
  })
  const suggestions = await api.post('/suggestions', {
    missing_skills: comparison.data.missing_skills,
    resume_text: resume.data.extracted_text,
  })
  return { resume: resume.data, job: job.data, comparison: comparison.data, suggestions: suggestions.data.suggestions }
}

export async function getInterviewTips(role) {
  const response = await api.get('/interview_tips', { params: { role } })
  return response.data
}

export async function updateResume(resumeText, acceptedSuggestions, acceptedSkills = []) {
  const response = await api.post('/update_resume', {
    resume_text: resumeText,
    accepted_suggestions: acceptedSuggestions,
    accepted_skills: acceptedSkills,
  })
  return response.data.updated_resume_text
}

export async function getAtsScore(resumeText, jobDescription) {
  const response = await api.post('/ats-score', {
    resume_text: resumeText,
    job_description: jobDescription,
  })
  return response.data
}

export async function getLearningPaths(missingSkills) {
  const response = await api.post('/learning-path', { missing_skills: missingSkills.slice(0, 20) })
  return response.data.paths
}

export async function rewriteForRole(resumeText, jobDescription) {
  const response = await api.post('/rewrite-resume', {
    resume_text: resumeText,
    job_description: jobDescription,
  })
  return response.data
}