"""Upload validation: type, size, signature, page and text limits."""

from __future__ import annotations

from io import BytesIO

from docx import Document

from config import get_settings


def _docx_bytes(text: str) -> bytes:
    document = Document()
    for line in text.splitlines():
        document.add_paragraph(line)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _post(client, filename: str, content: bytes, content_type: str):
    return client.post(
        "/upload_resume",
        files={"file": (filename, content, content_type)},
    )


class TestUploadValidation:
    def test_empty_file_is_rejected(self, client):
        response = _post(client, "resume.pdf", b"", "application/pdf")
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_unsupported_extension_is_rejected(self, client):
        response = _post(client, "resume.txt", b"hello", "text/plain")
        assert response.status_code == 400
        assert "PDF or DOCX" in response.json()["detail"]

    def test_invalid_pdf_signature_is_rejected(self, client):
        response = _post(client, "resume.pdf", b"not a pdf", "application/pdf")
        assert response.status_code == 400
        assert "valid PDF" in response.json()["detail"]

    def test_invalid_docx_signature_is_rejected(self, client):
        response = _post(client, "resume.docx", b"not a zip", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        assert response.status_code == 400
        assert "valid DOCX" in response.json()["detail"]

    def test_encrypted_pdf_is_rejected_before_parsing(self, client):
        content = b"%PDF-1.4\n1 0 obj\n<< /Encrypt 2 0 R >>\nendobj\n"
        response = _post(client, "resume.pdf", content, "application/pdf")
        assert response.status_code == 400
        assert "encrypted" in response.json()["detail"].lower()

    def test_oversized_upload_is_rejected(self, client, monkeypatch):
        settings = get_settings()
        monkeypatch.setattr(settings, "max_upload_bytes", 10)
        response = _post(client, "resume.pdf", b"%PDF-1.4\nmore than ten bytes", "application/pdf")
        assert response.status_code == 413
        assert "smaller than" in response.json()["detail"]

    def test_valid_docx_is_extracted(self, client):
        text = (
            "Avery Chen\n"
            "avery@example.com\n"
            "Skills\n"
            "Python, FastAPI, PostgreSQL\n"
            "Experience\n"
            "Software Engineer\n"
            "- Built REST APIs in Python.\n"
            "Education\n"
            "Bachelor of Science in Computer Science\n"
        )
        response = _post(
            client,
            "resume.docx",
            _docx_bytes(text),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert "Avery Chen" in body["extracted_text"]
        assert {"python", "fastapi", "postgresql"} <= set(body["skills"])
        assert "skills" in body["detected_sections"]
        assert body["word_count"] > 0
        assert body["structured_resume"]["contact"]["email"] == "avery@example.com"
        assert body["confidence"] > 0

    def test_unreadable_text_is_rejected(self, client):
        # A structurally valid DOCX with no paragraphs produces no text.
        response = _post(
            client,
            "resume.docx",
            _docx_bytes(""),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        assert response.status_code == 400
        assert "No readable text" in response.json()["detail"]
