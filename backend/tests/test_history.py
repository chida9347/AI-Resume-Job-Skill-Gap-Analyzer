"""Saved history, ownership isolation and privacy controls."""

from __future__ import annotations


def _save_resume(client, headers, text="Avery Chen\nSkills\nPython\n"):
    response = client.post(
        "/resumes",
        headers=headers,
        json={"filename": "cv.pdf", "text": text, "structured": {"skills": ["python"]}, "confidence": 80},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _save_job(client, headers):
    response = client.post(
        "/jobs",
        headers=headers,
        json={"title": "Backend Engineer", "company": "Acme", "text": "Required: Python, Docker."},
    )
    assert response.status_code == 201, response.text
    return response.json()


class TestSavedResources:
    def test_resume_job_and_analysis_round_trip(self, client, register):
        headers, _ = register()
        resume = _save_resume(client, headers)
        job = _save_job(client, headers)

        assert client.get("/resumes", headers=headers).json()[0]["id"] == resume["id"]
        assert client.get(f"/resumes/{resume['id']}", headers=headers).json()["text"].startswith("Avery")
        assert client.get("/jobs", headers=headers).json()[0]["id"] == job["id"]

        analysis = client.post(
            "/analyses",
            headers=headers,
            json={
                "resume_id": resume["id"],
                "job_id": job["id"],
                "role": "Backend Engineer",
                "comparison": {"required_coverage": 50},
                "ats": {"ats_score": 60},
                "suggestions": [],
                "learning_paths": [],
            },
        )
        assert analysis.status_code == 201, analysis.text
        analysis_id = analysis.json()["id"]
        listed = client.get("/analyses", headers=headers).json()
        assert listed[0]["id"] == analysis_id
        detail = client.get(f"/analyses/{analysis_id}", headers=headers).json()
        assert detail["ats"]["ats_score"] == 60

        assert client.delete(f"/resumes/{resume['id']}", headers=headers).status_code == 200
        assert client.get(f"/resumes/{resume['id']}", headers=headers).status_code == 404

    def test_analysis_cannot_reference_another_users_resume(self, client, register):
        first_headers, _ = register(email="first@example.com")
        resume = _save_resume(client, first_headers)

        second_headers, _ = register(email="second@example.com")
        response = client.post(
            "/analyses",
            headers=second_headers,
            json={"resume_id": resume["id"], "comparison": {}, "ats": {}},
        )
        assert response.status_code == 404


class TestOwnershipIsolation:
    def test_other_users_cannot_read_or_delete_resources(self, client, register):
        first_headers, _ = register(email="first@example.com")
        resume = _save_resume(client, first_headers)

        second_headers, _ = register(email="second@example.com")
        assert client.get(f"/resumes/{resume['id']}", headers=second_headers).status_code == 404
        assert client.delete(f"/resumes/{resume['id']}", headers=second_headers).status_code == 404
        # The owner can still read it.
        assert client.get(f"/resumes/{resume['id']}", headers=first_headers).status_code == 200

    def test_history_endpoints_require_authentication(self, client):
        for path in ("/resumes", "/jobs", "/analyses", "/interviews", "/history/export"):
            response = client.get(path)
            assert response.status_code == 401, path


class TestInterviewSessions:
    def test_session_answers_and_summary(self, client, register):
        headers, _ = register()
        questions = [
            {
                "id": "q1",
                "question": "Explain a list versus a tuple.",
                "category": "Programming fundamentals",
                "expected_concepts": ["mutable", "immutable"],
            }
        ]
        created = client.post(
            "/interviews",
            headers=headers,
            json={"role": "Backend Engineer", "questions": questions},
        )
        assert created.status_code == 201, created.text
        session_id = created.json()["id"]
        assert created.json()["question_count"] == 1
        assert created.json()["completed"] is False

        answer = client.post(
            f"/interviews/{session_id}/answers",
            headers=headers,
            json={
                "question": questions[0]["question"],
                "answer": (
                    "A list is mutable, so I can append to it. A tuple is immutable and hashable, "
                    "which makes it usable as a dictionary key. I choose tuples for fixed records."
                ),
                "category": questions[0]["category"],
                "expected_concepts": questions[0]["expected_concepts"],
            },
        )
        assert answer.status_code == 200, answer.text
        assert answer.json()["score"] > 0

        detail = client.get(f"/interviews/{session_id}", headers=headers).json()
        assert detail["completed"] is True
        assert detail["summary"]["attempts"] == 1
        assert detail["summary"]["average_score"] == answer.json()["score"]
        assert "not interview readiness" in detail["summary"]["disclaimer"]


class TestPrivacyControls:
    def test_export_contains_only_the_current_users_data(self, client, register):
        first_headers, _ = register(email="first@example.com")
        _save_resume(client, first_headers, "First user resume")
        second_headers, _ = register(email="second@example.com")
        _save_resume(client, second_headers, "Second user resume")

        export = client.get("/history/export", headers=first_headers)
        assert export.status_code == 200
        body = export.json()
        assert body["user"]["email"] == "first@example.com"
        assert [item["text"] for item in body["resumes"]] == ["First user resume"]

    def test_delete_all_removes_only_current_users_history(self, client, register):
        first_headers, _ = register(email="first@example.com")
        _save_resume(client, first_headers)
        second_headers, _ = register(email="second@example.com")
        _save_resume(client, second_headers)

        deleted = client.delete("/history", headers=first_headers)
        assert deleted.status_code == 200
        assert deleted.json()["status"] == "history_deleted"
        assert client.get("/resumes", headers=first_headers).json() == []
        assert len(client.get("/resumes", headers=second_headers).json()) == 1
