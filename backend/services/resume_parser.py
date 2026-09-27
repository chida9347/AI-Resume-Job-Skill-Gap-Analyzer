from pathlib import Path

from fastapi import HTTPException, UploadFile


async def extract_resume_text(file: UploadFile) -> str:
    suffix = Path(file.filename or "").suffix.lower()
    content = await file.read(10 * 1024 * 1024 + 1)
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Please upload a file smaller than 10 MB.")

    try:
        if suffix == ".pdf":
            from io import BytesIO
            from pypdf import PdfReader

            text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages)
        elif suffix == ".docx":
            from io import BytesIO
            from docx import Document

            document = Document(BytesIO(content))
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        else:
            raise HTTPException(status_code=400, detail="Upload a PDF or DOCX file.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Could not read this document. Try another PDF or DOCX.") from exc

    if not text.strip():
        raise HTTPException(status_code=400, detail="No readable text found. Scanned PDFs need OCR before analysis.")
    return text.strip()