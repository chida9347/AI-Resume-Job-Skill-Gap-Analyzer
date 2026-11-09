import axios from 'axios'

const ACCESS_KEY = 'roleprint.access_token'
const REFRESH_KEY = 'roleprint.refresh_token'
const USER_KEY = 'roleprint.user'
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const AUTH_EXPIRED_EVENT = 'roleprint:auth-expired'

function storage() {
  try {
    return window.localStorage
  } catch {
    return null
  }
}

export const tokenStore = {
  getAccess() {
    return storage()?.getItem(ACCESS_KEY) || ''
  },
  getRefresh() {
    return storage()?.getItem(REFRESH_KEY) || ''
  },
  getUser() {
    try {
      return JSON.parse(storage()?.getItem(USER_KEY) || 'null')
    } catch {
      return null
    }
  },
  setSession(session) {
    const target = storage()
    if (!target || !session) return
    if (session.access_token) target.setItem(ACCESS_KEY, session.access_token)
    if (session.refresh_token) target.setItem(REFRESH_KEY, session.refresh_token)
    if (session.user) target.setItem(USER_KEY, JSON.stringify(session.user))
  },
  setUser(user) {
    const target = storage()
    if (!target) return
    if (user) target.setItem(USER_KEY, JSON.stringify(user))
    else target.removeItem(USER_KEY)
  },
  clear() {
    const target = storage()
    if (!target) return
    target.removeItem(ACCESS_KEY)
    target.removeItem(REFRESH_KEY)
    target.removeItem(USER_KEY)
  },
}

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120000,
  headers: { Accept: 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = tokenStore.getAccess()
  if (token) {
    config.headers = { ...(config.headers || {}), Authorization: `Bearer ${token}` }
  }
  return config
})

let refreshPromise = null

async function refreshAccessToken() {
  const refreshToken = tokenStore.getRefresh()
  if (!refreshToken) throw new Error('No refresh token available.')
  const response = await axios.post(
    `${BASE_URL}/auth/refresh`,
    { refresh_token: refreshToken },
    { timeout: 30000, headers: { Accept: 'application/json' } },
  )
  tokenStore.setSession(response.data)
  return response.data.access_token
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const status = error.response?.status
    const url = original?.url || ''
    const isAuthEndpoint = url.includes('/auth/login') || url.includes('/auth/register') || url.includes('/auth/refresh')

    if (status !== 401 || !original || original._retried || isAuthEndpoint) {
      return Promise.reject(error)
    }

    original._retried = true
    try {
      if (!refreshPromise) {
        refreshPromise = refreshAccessToken().finally(() => {
          refreshPromise = null
        })
      }
      const token = await refreshPromise
      original.headers = { ...(original.headers || {}), Authorization: `Bearer ${token}` }
      return api(original)
    } catch (refreshError) {
      tokenStore.clear()
      window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT))
      return Promise.reject(refreshError)
    }
  },
)

// ---------------------------------------------------------------------------
// Authentication
// ---------------------------------------------------------------------------
export async function register(payload) {
  const { data } = await api.post('/auth/register', payload)
  tokenStore.setSession(data)
  return data
}

export async function login(payload) {
  const { data } = await api.post('/auth/login', payload)
  tokenStore.setSession(data)
  return data
}

export async function logout() {
  const refreshToken = tokenStore.getRefresh()
  try {
    if (refreshToken) await api.post('/auth/logout', { refresh_token: refreshToken })
  } finally {
    tokenStore.clear()
  }
}

export async function fetchMe() {
  const { data } = await api.get('/auth/me')
  tokenStore.setUser(data)
  return data
}

export async function updateProfile(payload) {
  const { data } = await api.patch('/auth/me', payload)
  tokenStore.setUser(data)
  return data
}

export async function changePassword(payload) {
  const { data } = await api.post('/auth/change-password', payload)
  return data
}

export async function deleteAccount(password) {
  try {
    const { data } = await api.delete('/auth/me', { data: { password } })
    return data
  } finally {
    tokenStore.clear()
  }
}

// ---------------------------------------------------------------------------
// Resume parsing and analysis
// ---------------------------------------------------------------------------
export async function uploadResume(file, onUploadProgress) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/upload_resume', form, { onUploadProgress })
  return data
}

export async function parseResume(text) {
  const { data } = await api.post('/parse-resume', { text })
  return data
}

export async function analyzeJob(text) {
  const { data } = await api.post('/analyze_job', { text })
  return data
}

export async function analyzeCombined({ resumeText, jobDescription, role = '', includeInterview = true }) {
  const { data } = await api.post('/analyze', {
    resume_text: resumeText,
    job_description: jobDescription,
    role,
    include_interview: includeInterview,
  })
  return data
}

export async function compareSkills(resumeSkills, jobSkills, preferredSkills = []) {
  const { data } = await api.post('/compare', {
    resume_skills: resumeSkills,
    job_skills: jobSkills,
    preferred_skills: preferredSkills,
  })
  return data
}

export async function getSuggestions(missingSkills, resumeText) {
  const { data } = await api.post('/suggestions', {
    missing_skills: missingSkills,
    resume_text: resumeText,
  })
  return data.suggestions
}

export async function updateResume(resumeText, acceptedSuggestions, acceptedSkills = []) {
  const { data } = await api.post('/update_resume', {
    resume_text: resumeText,
    accepted_suggestions: acceptedSuggestions,
    accepted_skills: acceptedSkills,
  })
  return data.updated_resume_text
}

// ---------------------------------------------------------------------------
// Explainable ATS, rewriting and editing
// ---------------------------------------------------------------------------
export async function getAtsScore(resumeText, jobDescription) {
  const { data } = await api.post('/ats-score', {
    resume_text: resumeText,
    job_description: jobDescription,
  })
  return data
}

export async function getLearningPaths(missingSkills, evidence, requirements) {
  const { data } = await api.post('/learning-path', {
    missing_skills: missingSkills.slice(0, 20),
    evidence: evidence || null,
    requirements: requirements || null,
  })
  return data.paths
}

export async function rewriteResume(resumeText, jobDescription, aiConsent = false) {
  const { data } = await api.post('/rewrite-resume', {
    resume_text: resumeText,
    job_description: jobDescription,
    ai_consent: aiConsent,
  })
  return data
}

export async function editResume(resumeText, instruction) {
  const { data } = await api.post('/edit-resume', {
    resume_text: resumeText,
    instruction,
  })
  return data
}

// ---------------------------------------------------------------------------
// Interviews
// ---------------------------------------------------------------------------
export async function generateInterviewQuestions(payload) {
  const { data } = await api.post('/interview/questions', payload)
  return data
}

export async function evaluateInterviewAnswer(payload) {
  const { data } = await api.post('/interview/evaluate', payload)
  return data
}

export async function getInterviewTips(role) {
  const { data } = await api.get('/interview_tips', { params: { role } })
  return data
}

// ---------------------------------------------------------------------------
// Multi-job matching
// ---------------------------------------------------------------------------
export async function rankJobs(resumeText, jobs, weights) {
  const { data } = await api.post('/job-match', {
    resume_text: resumeText,
    jobs: jobs.map((job) => ({
      id: job.id || '',
      title: job.title || '',
      company: job.company || '',
      text: job.text,
    })),
    weights: weights || null,
  })
  return data
}

// ---------------------------------------------------------------------------
// Saved history (authenticated)
// ---------------------------------------------------------------------------
export async function saveResume(payload) {
  const { data } = await api.post('/resumes', payload)
  return data
}
export async function listResumes() {
  const { data } = await api.get('/resumes')
  return data
}
export async function getResume(id) {
  const { data } = await api.get(`/resumes/${id}`)
  return data
}
export async function deleteResume(id) {
  const { data } = await api.delete(`/resumes/${id}`)
  return data
}

export async function saveJob(payload) {
  const { data } = await api.post('/jobs', payload)
  return data
}
export async function listJobs() {
  const { data } = await api.get('/jobs')
  return data
}
export async function getJob(id) {
  const { data } = await api.get(`/jobs/${id}`)
  return data
}
export async function deleteJob(id) {
  const { data } = await api.delete(`/jobs/${id}`)
  return data
}

export async function saveAnalysis(payload) {
  const { data } = await api.post('/analyses', payload)
  return data
}
export async function listAnalyses() {
  const { data } = await api.get('/analyses')
  return data
}
export async function getAnalysis(id) {
  const { data } = await api.get(`/analyses/${id}`)
  return data
}
export async function deleteAnalysis(id) {
  const { data } = await api.delete(`/analyses/${id}`)
  return data
}

export async function saveInterview(payload) {
  const { data } = await api.post('/interviews', payload)
  return data
}
export async function listInterviews() {
  const { data } = await api.get('/interviews')
  return data
}
export async function getInterview(id) {
  const { data } = await api.get(`/interviews/${id}`)
  return data
}
export async function submitInterviewAnswer(sessionId, payload) {
  const { data } = await api.post(`/interviews/${sessionId}/answers`, payload)
  return data
}
export async function deleteInterview(id) {
  const { data } = await api.delete(`/interviews/${id}`)
  return data
}

export async function exportHistory() {
  const { data } = await api.get('/history/export')
  return data
}
export async function deleteHistory() {
  const { data } = await api.delete('/history')
  return data
}

// ---------------------------------------------------------------------------
// Meta
// ---------------------------------------------------------------------------
export async function getHealth() {
  const { data } = await api.get('/health')
  return data
}

export { BASE_URL }
