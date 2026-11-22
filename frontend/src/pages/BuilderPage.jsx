import React from 'react'
import ResumeBuilder from '../components/ResumeBuilder.jsx'

export default function BuilderPage() {
  return (
    <section className="builder-page">
      <div className="page-heading">
        <div>
          <div className="eyebrow"><span className="eyebrow-line" /> Resume builder</div>
          <h1>Build your <span>resume.</span></h1>
          <p>
            Pick an ATS-friendly template and fill in your real details. The preview updates live and the final text is
            plain, standard-format resume content you can paste into an analysis.
          </p>
        </div>
      </div>

      <ResumeBuilder />
    </section>
  )
}
