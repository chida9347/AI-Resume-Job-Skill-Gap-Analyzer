import React from 'react'
import { Link } from 'react-router-dom'

export default function EmptyState({ icon: Icon, title, description, actionLabel, actionTo, onAction }) {
  return (
    <section className="empty-state">
      {Icon && <span className="empty-state-icon"><Icon size={22} /></span>}
      <h2>{title}</h2>
      {description && <p>{description}</p>}
      {actionLabel && actionTo && <Link className="button-primary" to={actionTo}>{actionLabel}</Link>}
      {actionLabel && onAction && <button className="button-primary" type="button" onClick={onAction}>{actionLabel}</button>}
    </section>
  )
}
