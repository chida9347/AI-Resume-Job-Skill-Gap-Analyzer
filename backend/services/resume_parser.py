"""Safe resume upload validation and text extraction.

Validation order: extension -> size -> magic bytes -> parser -> page/text limits.
Uploaded bytes are processed in memory and never written to disk, so the
anonymous flow leaves no resume copy behind.
"""

from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile

from config import get_settings

logger = logging.getLogger("roleprint.parser")

_ALLOWED_SUFFIXES = {".pdf", ".docx"}
_DOCX_MAGIC = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")


def _settings():
    return get_settings()


def _read_limited(content: bytes, limit: int) -> bytes:
    if len(content) > limit:
        raise HTTPException(
            status_code=413,
            detail=f"Please upload a file smaller than {limit // (1024 * 1024)} MB.",
        )
    return content


async def _read_upload(file: UploadFile) -> bytes:
    settings = _settings()
    # Read one byte over the limit so oversized files are detected without
    # buffering an arbitrarily large body.
    content = await file.read(settings.max_upload_bytes + 1)
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    return _read_limited(content, settings.max_upload_bytes)


def _validate_signature(suffix: str, content: bytes) -> None:
    if suffix == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise HTTPException(status_code=400, detail="The file does not appear to be a valid PDF.")
        if b"/Encrypt" in content[:4096]:
            raise HTTPException(
                status_code=400,
                detail="This PDF is encrypted. Remove the password protection and upload it again.",
            )
    elif suffix == ".docx":
        if not any(content.startswith(magic) for magic in _DOCX_MAGIC):
            raise HTTPException(
                status_code=400, detail="The file does not appear to be a valid DOCX document."
            )


def _extract_pdf(content: bytes) -> tuple[str, int]:
    from pypdf import PdfReader

    settings = _settings()
    try:
        reader = PdfReader(BytesIO(content))
        if reader.is_encrypted:
            raise HTTPException(
                status_code=400,
                detail="This PDF is encrypted. Remove the password protection and upload it again.",
            )
        page_count = len(reader.pages)
        if page_count > settings.max_pdf_pages:
            raise HTTPException(
                status_code=400,
                detail=f"This PDF has {page_count} pages; the limit is {settings.max_pdf_pages}.",
            )
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text, page_count
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail="Could not read this PDF. Try exporting it again or upload a DOCX."
        ) from exc


def _extract_docx(content: bytes) -> str:
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    try:
        document = Document(BytesIO(content))
        blocks: list[str] = []
        for child in document.element.body.iterchildren():
            if child.tag.endswith("}p"):
                blocks.append(Paragraph(child, document).text)
            elif child.tag.endswith("}tbl"):
                table = Table(child, document)
                blocks.extend("\t".join(cell.text for cell in row.cells) for row in table.rows)
        return "\n".join(blocks)
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail="Could not read this DOCX. Try saving it again or upload a PDF."
        ) from exc


def _ocr_pdf(content: bytes) -> str:
    """Optional OCR path for scanned PDFs.

    Requires ``pytesseract``, ``pdf2image`` and the Tesseract binary. The feature
    is opt-in through ENABLE_OCR so the default install stays lightweight.
    """
    settings = _settings()
    if not settings.enable_ocr:
        return ""
    try:
        import pytesseract
        from pdf2image import convert_from_bytes

        images = convert_from_bytes(content, dpi=200)
        if len(images) > settings.max_pdf_pages:
            images = images[: settings.max_pdf_pages]
        return "\n".join(pytesseract.image_to_string(image) for image in images)
    except Exception:
        logger.warning("OCR was requested but is unavailable; install pytesseract, pdf2image and Tesseract.")
        return ""


async def extract_resume_text(file: UploadFile) -> str:
    settings = _settings()
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail="Upload a PDF or DOCX file.")

    content = await _read_upload(file)
    _validate_signature(suffix, content)

    page_count = 0
    if suffix == ".pdf":
        text, page_count = _extract_pdf(content)
        if not text.strip():
            text = _ocr_pdf(content)
            if text.strip():
                logger.info("Scanned PDF processed with optional OCR (pages=%s).", page_count)
    else:
        text = _extract_docx(content)

    if not text.strip():
        detail = "No readable text found. If this is a scanned PDF, enable OCR or upload a text-based file."
        raise HTTPException(status_code=400, detail=detail)

    if len(text) > settings.max_resume_chars:
        raise HTTPException(
            status_code=400,
            detail="This document contains more text than the analysis limit. Upload a shorter resume.",
        )

    return text.strip()
