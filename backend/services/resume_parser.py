from pathlib import Path

from fastapi import HTTPException, UploadFile


async def extract_resume_text(file: UploadFile) -> str:
    suffix = Path(file.filename or "").suffix.lower()
    content = await file.read(10 * 1024 * 1024 + 1)
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Please upload a file smaller than 10 MB.")
    if suffix == ".pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="The file does not appear to be a valid PDF.")
    if suffix == ".docx" and not content.startswith(b"PK"):
        raise HTTPException(status_code=400, detail="The file does not appear to be a valid DOCX document.")

    try:
        if suffix == ".pdf":
            from io import BytesIO
            from pypdf import PdfReader

            text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages)
        elif suffix == ".docx":
            from io import BytesIO
            from docx import Document
            from docx.table import Table
            from docx.text.paragraph import Paragraph

            document = Document(BytesIO(content))
            blocks = []
            for child in document.element.body.iterchildren():
                if child.tag.endswith("}p"):
                    blocks.append(Paragraph(child, document).text)
                elif child.tag.endswith("}tbl"):
                    table = Table(child, document)
                    blocks.extend("\t".join(cell.text for cell in row.cells) for row in table.rows)
            text = "\n".join(blocks)
        else:
            raise HTTPException(status_code=400, detail="Upload a PDF or DOCX file.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Could not read this document. Try another PDF or DOCX.") from exc

    if not text.strip():
        raise HTTPException(status_code=400, detail="No readable text found. Scanned PDFs need OCR before analysis.")
    return text.strip()
