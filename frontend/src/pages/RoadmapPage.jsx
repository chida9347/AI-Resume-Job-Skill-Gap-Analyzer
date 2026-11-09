import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, BookOpenCheck, Target } from 'lucide-react'
import LearningPaths from '../components/LearningPaths.jsx'
import EmptyState from '../components/ui/EmptyState.jsx'
import { useWorkspace } from '../context/WorkspaceContext.jsx'

export default function RoadmapPage() {
  const { analysis, role } = useWorkspace()

  if (!analysis) {
    return (
      <EmptyState
        icon={BookOpenCheck}
        title="No roadmap yet"
        description="Run an analysis to turn missing or partially matched skills into practical learning goals."
        actionLabel="Run an analysis"
        actionTo="/analyze"
      />
    )
  }

  const comparison = analysis.comparison || {}
  const gaps = [
    ...(comparison.missing_required || comparison.missing_skills || []),
    ...(comparison.partial_required || []),
  ]
  const paths = analysis.learning_paths || []

  return (
    <section className="roadmap-page">
      <div className="page-heading">
        <div className="eyebrow"><span className="eyebrow-line" /> BUILD THE GAP</div>
        <h1>Learning <span>roadmap.</span></h1>
        <p>
          A study plan for {role || analysis.job?.title || 'your target role'}. These are suggestions, not proof of experience,
          and they do not guarantee a particular job outcome.
        </p>
      </div>

      <div className="roadmap-summary">
        <div><Target size={18} /><b>{gaps.length}</b><span>skills to explore</span></div>
        <div><BookOpenCheck size={18} /><b>{paths.length}</b><span>roadmaps generated</span></div>
        <Link className="text-button" to="/results"><ArrowLeft size={15} /> Back to results</Link>
      </div>

      <LearningPaths
        paths={paths}
        loading={false}
        error=""
        hasGaps={gaps.length > 0}
        title="Your next steps"
      />

      <div className="roadmap-note">
        <b>How to use this roadmap</b>
        <p>
          Start with the required skills you are most likely to need in the next role. Build one small project per skill,
          then add only the parts you genuinely completed to your resume. Re-run the analysis to see how the evidence changes.
        </p>
      </div>
    </section>
  )
}
