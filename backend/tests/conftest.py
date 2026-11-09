"""Shared pytest fixtures.

Environment variables are set before the application package is imported so the
engine, settings cache and middleware all use an isolated test database. No test
touches the developer's local roleprint.db.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

_DB_PATH = Path(tempfile.gettempdir()) / "roleprint_pytest.db"

os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH.as_posix()}"
os.environ["JWT_SECRET"] = "pytest-secret-key-that-is-long-enough-123456"
os.environ["ENABLE_SEMANTIC_MATCHING"] = "false"
os.environ["ENABLE_RATE_LIMIT"] = "false"
os.environ["ENABLE_OPENAI_REWRITER"] = "false"
os.environ["ENABLE_OCR"] = "false"
os.environ["ENVIRONMENT"] = "test"

from fastapi.testclient import TestClient  # noqa: E402

from database import Base, engine  # noqa: E402
from main import app  # noqa: E402
from middleware import RateLimitMiddleware  # noqa: E402
from models import db as _db_models  # noqa: F401,E402  (register mappings)


@pytest.fixture(autouse=True)
def isolated_database():
    """Recreate the schema and clear the limiter before every test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    RateLimitMiddleware._hits.clear()
    yield
    Base.metadata.drop_all(bind=engine)
    RateLimitMiddleware._hits.clear()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def register(client):
    def _register(email: str = "avery@example.com", password: str = "StrongPass1!"):
        response = client.post(
            "/auth/register",
            json={"email": email, "password": password, "full_name": "Avery Chen"},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        return {"Authorization": f"Bearer {body['access_token']}"}, body

    return _register


@pytest.fixture
def sample_resume() -> str:
    return (
        "Avery Chen\n"
        "avery@example.com\n"
        "+1 555 0100\n"
        "Summary\n"
        "Backend engineer focused on Python APIs.\n"
        "Skills\n"
        "Python, FastAPI, PostgreSQL, React\n"
        "Experience\n"
        "Software Engineer, Acme Corp, 2021 - 2024\n"
        "- Built REST APIs in Python, improving response time by 20%.\n"
        "Education\n"
        "Bachelor of Science in Computer Science\n"
        "Projects\n"
        "Roleprint - Built a FastAPI service with PostgreSQL and React.\n"
    )


@pytest.fixture
def sample_job() -> str:
    return (
        "Backend Engineer\n"
        "Required: Python, FastAPI, PostgreSQL, Docker.\n"
        "Preferred: Kubernetes, AWS.\n"
        "3+ years of experience.\n"
        "Bachelor degree required.\n"
    )
