import React from 'react'
import { Link } from 'react-router-dom'
import { ScanSearch } from 'lucide-react'
import ResultsView from '../components/results/ResultsView.jsx'
import EmptyState from '../components/ui/EmptyState.jsx'
import { useWorkspace } from '../context/WorkspaceContext.jsx'

export default function ResultsPage() {
  const { analysis, savedToHistory, savedAnalysisId, saveWarning } = useWorkspace()

  if (!analysis) {
    return (
      <EmptyState
        icon={ScanSearch}
        title="No analysis yet"
        description="Add a resume and a job description to see skill evidence, an explainable ATS estimate, learning paths and interview questions."
        actionLabel="Start an analysis"
        actionTo="/analyze"
      />
    )
  }

  return (
    <section className="results-page-wrapper">
      {savedToHistory && savedAnalysisId && (
        <div className="editor-note" role="status">
          <ScanSearch size={17} />
          <div>
            <b>Saved to your private history</b>
            <span>You can reopen this snapshot from your history at any time. <Link to={`/analyses/${savedAnalysisId}`}>Open saved copy</Link></span>
          </div>
        </div>
      )}
      {saveWarning && <p className="error-banner" role="alert">{saveWarning}</p>}
      <ResultsView analysis={analysis} />
    </section>
  )
}
