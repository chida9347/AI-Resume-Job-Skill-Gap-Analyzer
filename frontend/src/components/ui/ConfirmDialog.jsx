import React, { useEffect, useRef } from 'react'
import { LoaderCircle, X } from 'lucide-react'

export default function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  tone = 'default',
  busy = false,
  onConfirm,
  onCancel,
}) {
  const confirmRef = useRef(null)

  useEffect(() => {
    if (!open) return undefined
    const previous = document.activeElement
    confirmRef.current?.focus()
    function handleKey(event) {
      if (event.key === 'Escape' && !busy) onCancel?.()
    }
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('keydown', handleKey)
      previous?.focus?.()
    }
  }, [open, busy, onCancel])

  if (!open) return null

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => {
      if (event.target === event.currentTarget && !busy) onCancel?.()
    }}>
      <div className="modal-card" role="dialog" aria-modal="true" aria-labelledby="confirm-dialog-title">
        <button className="modal-close" type="button" onClick={onCancel} disabled={busy} aria-label="Close dialog">
          <X size={17} />
        </button>
        <h2 id="confirm-dialog-title">{title}</h2>
        {description && <p>{description}</p>}
        <div className="modal-actions">
          <button className="button-secondary" type="button" onClick={onCancel} disabled={busy}>
            {cancelLabel}
          </button>
          <button
            ref={confirmRef}
            className={`button-primary ${tone === 'danger' ? 'button-danger' : ''}`}
            type="button"
            onClick={onConfirm}
            disabled={busy}
          >
            {busy && <LoaderCircle className="spin" size={15} />}
            {busy ? 'Working…' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
