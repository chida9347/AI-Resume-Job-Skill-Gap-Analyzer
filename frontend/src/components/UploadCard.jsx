import React from 'react'
import { FileText, FileUp } from 'lucide-react'

export default function UploadCard({ file, inputRef, onFileSelect }) {
  function dropFile(event) {
    event.preventDefault()
    onFileSelect(event.dataTransfer.files[0])
  }

  return <section className="input-section upload-card">
    <div className="section-heading"><span className="section-index">01</span><div><h2>Your resume</h2><p>PDF or DOCX · up to 10 MB</p></div></div>
    <input ref={inputRef} className="visually-hidden" type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={(event) => onFileSelect(event.target.files?.[0])} />
    <button type="button" className={`dropzone ${file ? 'has-file' : ''}`} onClick={() => inputRef.current?.click()} onDragOver={(event) => event.preventDefault()} onDrop={dropFile}>
      {file ? <><span className="drop-icon"><FileText size={23} /></span><span className="drop-title">{file.name}</span><span className="drop-subtitle">{(file.size / 1024 / 1024).toFixed(2)} MB · Ready to analyze</span><span className="change-file">Choose a different file</span></> : <><span className="drop-icon"><FileUp size={23} /></span><span className="drop-title">Drop your resume here</span><span className="drop-subtitle">or <span>browse files</span> on your device</span><span className="drop-formats">PDF <i /> DOCX</span></>}
    </button>
  </section>
}