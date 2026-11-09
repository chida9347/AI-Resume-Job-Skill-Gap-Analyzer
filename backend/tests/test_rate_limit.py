"""Rate limiting and centralized error handling."""

from __future__ import annotations

from config import get_settings
from middleware import RateLimitMiddleware


class TestRateLimiting:
    def test_requests_are_limited_per_path(self, client, monkeypatch):
        settings = get_settings()
        monkeypatch.setattr(settings, "enable_rate_limit", True)
        monkeypatch.setattr(settings, "rate_limit_requests", 2)
        monkeypatch.setattr(settings, "rate_limit_window_seconds", 60)
        RateLimitMiddleware._hits.clear()

        payload = {"resume_skills": ["python"], "job_skills": ["python"]}
        assert client.post("/compare", json=payload).status_code == 200
        assert client.post("/compare", json=payload).status_code == 200
        limited = client.post("/compare", json=payload)
        assert limited.status_code == 429
        assert limited.headers.get("retry-after")
        body = limited.json()
        assert body["detail"]
        assert body["error"]["code"] == "rate_limited"

    def test_health_is_exempt_from_rate_limiting(self, client, monkeypatch):
        settings = get_settings()
        monkeypatch.setattr(settings, "enable_rate_limit", True)
        monkeypatch.setattr(settings, "rate_limit_requests", 1)
        RateLimitMiddleware._hits.clear()
        for _ in range(5):
            assert client.get("/health").status_code == 200

    def test_limiter_is_disabled_by_default_in_tests(self, client):
        # conftest disables the limiter so functional tests are not rate-limited.
        settings = get_settings()
        assert settings.enable_rate_limit is False
        for _ in range(5):
            assert client.get("/").status_code == 200


class TestErrorHandling:
    def test_unknown_route_returns_structured_error(self, client):
        response = client.get("/does-not-exist")
        assert response.status_code == 404
        body = response.json()
        assert body["detail"]
        assert body["error"]["code"] == "http_error"

    def test_method_not_allowed_keeps_detail(self, client):
        response = client.get("/analyze")
        assert response.status_code == 405
        assert response.json()["detail"]

    def test_invalid_json_returns_validation_error(self, client):
        response = client.post(
            "/analyze",
            content=b"{not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "validation_error"
