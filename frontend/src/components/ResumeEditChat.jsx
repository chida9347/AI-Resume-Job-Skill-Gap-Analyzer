import React, { useState } from 'react'
import { LoaderCircle, MessageCircle, Send, Sparkles } from 'lucide-react'

export default function ResumeEditChat({ onSend, disabled = false }) {
  const [instruction, setInstruction] = useState('')
  const [messages, setMessages] = useState([
    { id: 'welcome', role: 'assistant', text: 'Tell me what you want to change. I’ll update the resume text above and show you what changed.' },
  ])
  const [sending, setSending] = useState(false)

  async function submit(event) {
    event.preventDefault()
    const request = instruction.trim()
    if (!request || sending || disabled) return
    setMessages((current) => [...current, { id: crypto.randomUUID(), role: 'user', text: request }])
    setInstruction('')
    setSending(true)
    try {
      const result = await onSend(request)
      setMessages((current) => [...current, {
        id: crypto.randomUUID(),
        role: 'assistant',
        text: result.reply,
        changeSummary: result.change_summary,
        changed: result.changed,
        method: result.method,
      }])
    } catch (error) {
      const detail = error?.response?.data?.detail
      setMessages((current) => [...current, {
        id: crypto.randomUUID(),
        role: 'assistant',
        text: typeof detail === 'string' ? detail : 'I could not update the resume. Your current text is unchanged; please try again.',
      }])
    } finally {
      setSending(false)
    }
  }

  return <section className="resume-chat" aria-labelledby="resume-chat-title">
    <div className="resume-chat-heading">
      <div className="resume-chat-icon"><MessageCircle size={18} /></div>
      <div><h2 id="resume-chat-title">Ask for a resume edit</h2><p>Request a change in plain language. Review the text before downloading.</p></div>
    </div>
    <div className="resume-chat-messages" role="log" aria-live="polite" aria-relevant="additions text">
      {messages.map((message) => <article className={`resume-chat-message ${message.role === 'user' ? 'is-user' : 'is-assistant'}`} key={message.id}>
        <div className="resume-chat-bubble">{message.role === 'assistant' && <Sparkles size={14} />}<p>{message.text}</p></div>
        {message.changeSummary && <span className={`resume-chat-change ${message.changed ? '' : 'is-unchanged'}`}>{message.changeSummary}{message.method === 'openai' ? ' · AI-assisted' : ''}</span>}
      </article>)}
      {sending && <div className="resume-chat-pending"><LoaderCircle className="spin" size={15} /> Applying your request…</div>}
    </div>
    <form className="resume-chat-form" onSubmit={submit}>
      <label className="sr-only" htmlFor="resume-edit-instruction">Describe the resume change</label>
      <textarea id="resume-edit-instruction" value={instruction} onChange={(event) => setInstruction(event.target.value)} maxLength={2000} rows={2} placeholder={'e.g. Replace “worked on reports” with “built weekly sales reports”, or fit this resume on one page'} disabled={sending || disabled} />
      <button className="button-primary" type="submit" disabled={!instruction.trim() || sending || disabled}>
        {sending ? <LoaderCircle className="spin" size={16} /> : <Send size={16} />}<span>{sending ? 'Updating' : 'Apply edit'}</span>
      </button>
    </form>
    <p className="resume-chat-footnote">Only the current resume draft is edited. You can keep revising it, then download the PDF when you’re ready.</p>
  </section>
}
