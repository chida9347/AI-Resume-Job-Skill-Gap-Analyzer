import { jsPDF } from 'jspdf'

/**
 * Render the editable resume text into a clean, readable PDF.
 *
 * This deliberately does not attempt to reproduce the uploaded document's
 * original visual layout. It formats the text the user has reviewed and
 * approved in the editor.
 */
export function downloadTextAsPdf({
  text,
  filename = 'updated-resume.pdf',
  targetRole = '',
  fitToOnePage = false,
  onError = () => {},
}) {
  if (!text?.trim()) return false

  const pdf = new jsPDF({ unit: 'pt', format: 'letter' })
  const pageWidth = pdf.internal.pageSize.getWidth()
  const pageHeight = pdf.internal.pageSize.getHeight()
  const margin = fitToOnePage ? 30 : 54
  const contentWidth = pageWidth - margin * 2
  const sourceLines = text.replace(/\r/g, '').split('\n')
  const firstContentIndex = sourceLines.findIndex((line) => line.trim())
  const headingPattern =
    /^\s*((?:(?:professional|technical)\s+)?(?:summary|profile|objective|experience|employment history|work history|skills|education|certifications?|projects?|awards?))\s*:?\s*(.*)$/i
  let name = 'Resume'

  if (firstContentIndex >= 0 && !headingPattern.test(sourceLines[firstContentIndex])) {
    name = sourceLines[firstContentIndex].trim()
    sourceLines.splice(firstContentIndex, 1)
  }

  const preamble = []
  const sections = []
  let currentSection = null
  for (const line of sourceLines) {
    const heading = line.match(headingPattern)
    if (heading) {
      currentSection = { title: heading[1].trim(), lines: [] }
      sections.push(currentSection)
      if (heading[2].trim()) currentSection.lines.push(heading[2].trim())
    } else if (currentSection) {
      currentSection.lines.push(line)
    } else if (line.trim()) {
      preamble.push(line.trim())
    }
  }

  pdf.setDrawColor(36, 75, 62)
  pdf.setLineWidth(3)
  pdf.line(margin, 35, pageWidth - margin, 35)
  let y = fitToOnePage ? 43 : 70
  pdf.setTextColor(24, 33, 31)
  pdf.setFont('helvetica', 'bold')
  pdf.setFontSize(fitToOnePage ? 16 : 23)
  pdf.text(name, margin, y)
  y += fitToOnePage ? 12 : 18

  if (targetRole.trim()) {
    pdf.setTextColor(87, 105, 82)
    pdf.setFont('helvetica', 'normal')
    pdf.setFontSize(fitToOnePage ? 7 : 9)
    pdf.text(`TARGET ROLE  |  ${targetRole.trim()}`, margin, y)
    y += fitToOnePage ? 9 : 15
  }

  if (preamble.length) {
    pdf.setTextColor(91, 99, 93)
    pdf.setFont('helvetica', 'normal')
    pdf.setFontSize(fitToOnePage ? 7 : 9)
    for (const line of preamble) {
      const wrapped = pdf.splitTextToSize(line, contentWidth)
      for (const row of wrapped) {
        pdf.text(row, margin, y)
        y += fitToOnePage ? 8 : 12
      }
    }
  }

  y += fitToOnePage ? 2 : 4
  pdf.setDrawColor(218, 222, 212)
  pdf.setLineWidth(0.7)
  pdf.line(margin, y, pageWidth - margin, y)
  y += fitToOnePage ? 9 : 18
  let didOverflow = false

  function ensureSpace(height) {
    if (y + height > pageHeight - (fitToOnePage ? 30 : 48)) {
      if (fitToOnePage) {
        didOverflow = true
        return
      }
      pdf.addPage()
      y = 52
    }
  }

  function writeBodyLine(rawLine, isExperience = false) {
    const trimmed = rawLine.trim()
    if (!trimmed) {
      y += fitToOnePage ? 2 : 5
      return
    }
    const bulletMatch = trimmed.match(/^(?:[-*+]\s+|\d+[.)]\s+)(.*)$/)
    const accomplishment =
      /^(?:built|created|developed|designed|implemented|delivered|led|launched|improved|increased|reduced|optimized|automated|analyzed|managed|maintained|migrated|deployed|engineered|generated|established|streamlined|resolved|integrated|collaborated|supported|configured|tested|wrote|conducted|coordinated|owned|mentored|achieved|introduced)\b/i.test(
        trimmed,
      )
    const isBullet = Boolean(bulletMatch) || (isExperience && accomplishment)
    const content = bulletMatch ? bulletMatch[1] : trimmed
    const indent = isBullet ? 14 : 0
    const rows = pdf.splitTextToSize(content, contentWidth - indent)
    pdf.setFont('helvetica', 'normal')
    pdf.setFontSize(fitToOnePage ? 7 : 10)
    pdf.setTextColor(45, 53, 48)
    for (let index = 0; index < rows.length; index += 1) {
      ensureSpace(fitToOnePage ? 8 : 14)
      if (didOverflow) return
      if (isBullet && index === 0) {
        pdf.setFillColor(119, 148, 72)
        pdf.circle(margin + 3, y - 3, 1.6, 'F')
      }
      pdf.text(rows[index], margin + indent, y)
      y += fitToOnePage ? 8 : 14
    }
  }

  for (const section of sections) {
    if (!section.lines.some((line) => line.trim())) continue
    ensureSpace(fitToOnePage ? 20 : 34)
    if (didOverflow) break
    pdf.setFont('helvetica', 'bold')
    pdf.setFontSize(fitToOnePage ? 8 : 11)
    pdf.setTextColor(36, 75, 62)
    pdf.text(section.title.toUpperCase(), margin, y)
    y += fitToOnePage ? 4 : 7
    pdf.setDrawColor(221, 226, 215)
    pdf.setLineWidth(0.6)
    pdf.line(margin, y, pageWidth - margin, y)
    y += fitToOnePage ? 7 : 14
    const isExperience = /experience|employment history|work history/i.test(section.title)
    for (const line of section.lines) writeBodyLine(line, isExperience)
    y += fitToOnePage ? 3 : 7
  }

  if (!sections.length) {
    for (const line of preamble) writeBodyLine(line)
  }

  const pageCount = pdf.getNumberOfPages()
  if (fitToOnePage && didOverflow) {
    onError(
      'This resume is too long to fit legibly on one page without removing content. Shorten the text and try again.',
    )
    return false
  }

  for (let pageNumber = 1; pageNumber <= pageCount; pageNumber += 1) {
    pdf.setPage(pageNumber)
    pdf.setFont('helvetica', 'normal')
    pdf.setFontSize(8)
    pdf.setTextColor(126, 133, 125)
    pdf.text(`${name}  |  ${pageNumber}`, pageWidth - margin, pageHeight - 24, { align: 'right' })
  }

  const downloadUrl = URL.createObjectURL(pdf.output('blob'))
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = filename
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000)
  return true
}

export function downloadJson(data, filename) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}
