import React from 'react'
import { BriefcaseBusiness } from 'lucide-react'

export default function JobInput({ role, onRoleChange, description, onDescriptionChange }) {
  return <section className="input-section job-section">
    <div className="section-heading"><span className="section-index">02</span><div><h2>Job description</h2><p>Paste the full listing for the best comparison</p></div></div>
    <textarea className="job-textarea" value={description} onChange={(event) => onDescriptionChange(event.target.value)} placeholder={'Paste the job description here...\n\nInclude responsibilities and qualifications so we can spot the most relevant skills.'} maxLength={100000} />
    <div className="textarea-footer"><span>Only used to create this analysis</span><span>{description.length.toLocaleString()} / 100,000</span></div>
    <label className="field-label" htmlFor="role">Target role <span>OPTIONAL</span></label>
    <div className="role-input"><BriefcaseBusiness size={17} /><input id="role" value={role} onChange={(event) => onRoleChange(event.target.value)} placeholder="e.g. Senior Product Designer" /></div>
  </section>
}