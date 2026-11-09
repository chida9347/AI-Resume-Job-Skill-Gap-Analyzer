import React, { createContext, useCallback, useContext, useMemo, useState } from 'react'
import * as api from '../services/api.js'
import { getErrorMessage } from '../utils/errors.js'
import { useAuth } from './AuthContext.jsx'

const WorkspaceContext = createContext(null)

function initialWorkspace() {
  return {
    file: null,
    jobDescription: '',
    role: '',
    analysis: null,
    resumeText: '',
    resumeMeta: null,
    savedAnalysisId: '',
    savedToHistory: false,
    saveWarning: '',
    error: '',
    busy: false,
    progress: 0,
    appliedSkills: [],
    appliedReviewNotes: 0,
    appliedRewrite: false,
    fitToOnePage: false,
  }
}

export function WorkspaceProvider({ children }) {
  const { isAuthenticated } = useAuth()
  const [state, setState] = useState(initialWorkspace)

  const patch = useCallback((changes) => {
    setState((current) => ({ ...current, ...changes }))
  }, [])

  const setFile = useCallback((file) => patch({ file, error: '' }), [patch])
  const setJobDescription = useCallback((jobDescription) => patch({ jobDescription }), [patch])
  const setRole = useCallback((role) => patch({ role }), [patch])
  const setResumeText = useCallback((resumeText) => patch({ resumeText }), [patch])
  const setFitToOnePage = useCallback((fitToOnePage) => patch({ fitToOnePage }), [patch])
  const setError = useCallback((error) => patch({ error }), [patch])

  const runAnalysis = useCallback(
    async ({ file, resumeText: pastedText, jobDescription, role, saveToHistory = false }) => {
      patch({ busy: true, error: '', progress: 0, saveWarning: '' })
      try {
        let text = (pastedText || '').trim()
        let meta = null

        if (file) {
          const uploaded = await api.uploadResume(file, (event) => {
            if (!event.total) return
            patch({ progress: Math.round((event.loaded / event.total) * 45) })
          })
          text = uploaded.extracted_text
          meta = uploaded
        } else if (text) {
          try {
            const parsed = await api.parseResume(text)
            meta = {
              filename: 'pasted-resume.txt',
              extracted_text: text,
              skills: parsed.skills,
              structured_resume: parsed.structured_resume,
              confidence: parsed.confidence,
              warnings: parsed.warnings,
              extraction_confidence:
                parsed.confidence >= 75 ? 'high' : parsed.confidence >= 45 ? 'medium' : 'low',
              word_count: parsed.structured_resume?.word_count || text.split(/\s+/).filter(Boolean).length,
              detected_sections: Object.entries(parsed.structured_resume?.section_presence || {})
                .filter(([, present]) => present)
                .map(([key]) => key),
            }
          } catch {
            meta = null
          }
        }

        if (!text) throw new Error('Add a resume file or paste your resume text to continue.')

        patch({ progress: 60 })
        const analysis = await api.analyzeCombined({
          resumeText: text,
          jobDescription,
          role,
        })

        // The rewrite draft is an optional extra; a failure must not discard the
        // main analysis. It is never applied automatically.
        let rewrite = null
        let rewriteError = ''
        try {
          rewrite = await api.rewriteResume(text, jobDescription, false)
        } catch (rewriteFailure) {
          rewriteError = getErrorMessage(rewriteFailure, 'The role-specific rewrite is unavailable.')
        }

        const nextAnalysis = { ...analysis, rewrite, rewriteError }
        patch({
          analysis: nextAnalysis,
          resumeText: text,
          resumeMeta: meta,
          file: file || null,
          jobDescription,
          role: role || analysis?.interview?.role || analysis?.job?.title || '',
          appliedSkills: [],
          appliedReviewNotes: 0,
          appliedRewrite: false,
          fitToOnePage: false,
          savedAnalysisId: '',
          savedToHistory: false,
          progress: 80,
        })

        let savedAnalysisId = ''
        let saveWarning = ''
        if (saveToHistory && isAuthenticated) {
          try {
            const savedResume = await api.saveResume({
              filename: file?.name || 'pasted-resume.txt',
              text,
              structured: analysis.structured_resume || {},
              confidence: analysis.meta?.resume_confidence || 0,
              warnings: analysis.meta?.resume_warnings || [],
            })
            const savedJob = await api.saveJob({
              title: analysis.job?.title || '',
              company: analysis.job?.company || '',
              text: jobDescription,
              structured: analysis.job || {},
            })
            const savedAnalysis = await api.saveAnalysis({
              resume_id: savedResume.id,
              job_id: savedJob.id,
              role: role || analysis?.interview?.role || analysis?.job?.title || '',
              comparison: analysis.comparison || {},
              ats: analysis.ats || {},
              suggestions: analysis.suggestions || [],
              learning_paths: analysis.learning_paths || [],
            })
            savedAnalysisId = savedAnalysis.id
          } catch (saveFailure) {
            saveWarning = getErrorMessage(
              saveFailure,
              'The analysis is ready, but it could not be saved to your history.',
            )
          }
        }

        patch({
          busy: false,
          progress: 100,
          savedAnalysisId,
          savedToHistory: Boolean(savedAnalysisId),
          saveWarning,
        })
        return nextAnalysis
      } catch (error) {
        const message = getErrorMessage(error, 'The analysis could not be completed. Check the API connection and try again.')
        patch({ busy: false, progress: 0, error: message })
        throw error
      }
    },
    [isAuthenticated, patch],
  )

  const applySuggestions = useCallback(
    async (selectedItems) => {
      const confirmedSkills = selectedItems.filter((item) => item.kind === 'skill').map((item) => item.skill)
      const reviewNotes = selectedItems.filter((item) => item.kind !== 'skill').map((item) => item.text)
      const updated = await api.updateResume(state.resumeText, reviewNotes, confirmedSkills)
      patch({
        resumeText: updated,
        appliedSkills: confirmedSkills,
        appliedReviewNotes: reviewNotes.length,
        appliedRewrite: false,
      })
      return updated
    },
    [patch, state.resumeText],
  )

  const applyRewrite = useCallback(
    (rewritten) => {
      if (!rewritten) return
      patch({ resumeText: rewritten, appliedRewrite: true, appliedSkills: [], appliedReviewNotes: 0 })
    },
    [patch],
  )

  const applyChatEdit = useCallback(
    async (instruction) => {
      const result = await api.editResume(state.resumeText, instruction)
      if (result.changed) patch({ resumeText: result.updated_resume_text })
      if (typeof result.fit_to_one_page === 'boolean') patch({ fitToOnePage: result.fit_to_one_page })
      return result
    },
    [patch, state.resumeText],
  )

  const loadSavedAnalysis = useCallback(
    (detail) => {
      patch({
        analysis: {
          comparison: detail.comparison || {},
          ats: detail.ats || {},
          suggestions: detail.suggestions || [],
          learning_paths: detail.learning_paths || [],
          interview: { role: detail.role || '', questions: [], tips: [] },
          structured_resume: {},
          resume_skills: [],
          job: {},
          meta: { saved: true },
          rewrite: null,
          rewriteError: '',
        },
        role: detail.role || '',
        savedAnalysisId: detail.id,
        savedToHistory: true,
        resumeText: '',
        jobDescription: '',
        file: null,
        resumeMeta: null,
        appliedSkills: [],
        appliedReviewNotes: 0,
        appliedRewrite: false,
        error: '',
      })
    },
    [patch],
  )

  const resetWorkspace = useCallback(() => setState(initialWorkspace()), [])

  const value = useMemo(
    () => ({
      ...state,
      hasAnalysis: Boolean(state.analysis),
      setFile,
      setJobDescription,
      setRole,
      setResumeText,
      setFitToOnePage,
      setError,
      runAnalysis,
      applySuggestions,
      applyRewrite,
      applyChatEdit,
      loadSavedAnalysis,
      resetWorkspace,
    }),
    [
      state,
      setFile,
      setJobDescription,
      setRole,
      setResumeText,
      setFitToOnePage,
      setError,
      runAnalysis,
      applySuggestions,
      applyRewrite,
      applyChatEdit,
      loadSavedAnalysis,
      resetWorkspace,
    ],
  )

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext)
  if (!context) throw new Error('useWorkspace must be used inside WorkspaceProvider')
  return context
}
