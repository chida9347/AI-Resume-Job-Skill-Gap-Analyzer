"""API smoke tests and backward-compatibility contracts."""

from __future__ import annotations


def _analyze(client, sample_resume, sample_job):
    response = client.post(
        "/analyze",
        json={"resume_text": sample_resume, "job_description": sample_job},
    )
    assert response.status_code == 200, response.text
    return response.json()


class TestMetaEndpoints:
    def test_health_and_root(self, client):
        health = client.get("/health")
        assert health.status_code == 200
        body = health.json()
        assert body["status"] == "ok"
        assert "features" in body

        root = client.get("/")
        assert root.status_code == 200
        assert root.json()["docs"] == "/docs"

    def test_request_id_is_returned(self, client):
        response = client.get("/health")
        assert response.headers.get("x-request-id")


class TestCombinedAnalysis:
    def test_analyze_returns_all_sections(self, client, sample_resume, sample_job):
        body = _analyze(client, sample_resume, sample_job)
        for key in (
            "structured_resume",
            "resume_skills",
            "job",
            "comparison",
            "ats",
            "suggestions",
            "learning_paths",
            "interview",
            "meta",
        ):
            assert key in body

        assert body["comparison"]["required_coverage"] > 0
        assert body["ats"]["ats_score"] <= 97
        assert body["meta"]["method"].startswith("hybrid")
        assert body["interview"]["questions"]

    def test_analysis_is_deterministic(self, client, sample_resume, sample_job):
        first = _analyze(client, sample_resume, sample_job)
        second = _analyze(client, sample_resume, sample_job)
        assert first["ats"]["ats_score"] == second["ats"]["ats_score"]
        assert first["comparison"]["required_coverage"] == second["comparison"]["required_coverage"]

    def test_interview_can_be_disabled(self, client, sample_resume, sample_job):
        response = client.post(
            "/analyze",
            json={
                "resume_text": sample_resume,
                "job_description": sample_job,
                "include_interview": False,
            },
        )
        assert response.status_code == 200
        assert response.json()["interview"]["questions"] == []

    def test_empty_input_is_a_validation_error_with_compatible_detail(self, client):
        response = client.post("/analyze", json={"resume_text": "", "job_description": "Python"})
        assert response.status_code == 422
        body = response.json()
        assert body["detail"]
        assert body["error"]["code"] == "validation_error"
        assert body["error"]["details"]


class TestLegacyEndpoints:
    def test_ats_score_and_alias(self, client, sample_resume, sample_job):
        payload = {"resume_text": sample_resume, "job_description": sample_job}
        for path in ("/ats_score", "/ats-score"):
            response = client.post(path, json=payload)
            assert response.status_code == 200, path
            body = response.json()
            assert "ats_score" in body
            assert "score_breakdown" in body
            assert "section_score" in body

    def test_learning_path_and_alias(self, client):
        for path in ("/learning_path", "/learning-path"):
            response = client.post(path, json={"missing_skills": ["Docker"]})
            assert response.status_code == 200, path
            path_body = response.json()["paths"][0]
            assert path_body["skill"] == "Docker"
            assert len(path_body["roadmap"]) == 4
            assert path_body["project"]

    def test_rewrite_resume_and_alias(self, client):
        payload = {
            "resume_text": "EXPERIENCE\n- Worked on Python APIs.\n",
            "job_description": "Python engineer.",
        }
        for path in ("/rewrite_resume", "/rewrite-resume"):
            response = client.post(path, json=payload)
            assert response.status_code == 200, path
            assert response.json()["method"] == "rule-based"

    def test_parse_resume(self, client, sample_resume):
        response = client.post("/parse-resume", json={"text": sample_resume})
        assert response.status_code == 200
        body = response.json()
        assert body["skills"]
        assert body["structured_resume"]["contact"]["email"] == "avery@example.com"

    def test_analyze_job(self, client, sample_job):
        response = client.post("/analyze_job", json={"text": sample_job})
        assert response.status_code == 200
        assert response.json()["technical_skills"]

    def test_compare(self, client):
        response = client.post(
            "/compare",
            json={
                "resume_skills": ["python"],
                "job_skills": ["python", "docker"],
                "preferred_skills": ["aws"],
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["matched_skills"] == ["python"]
        assert body["missing_skills"] == ["docker"]
        assert body["matched_preferred_skills"] == []

    def test_suggestions_and_update_resume(self, client):
        suggestions = client.post(
            "/suggestions",
            json={"missing_skills": ["docker"], "resume_text": "Skills\nPython\n"},
        )
        assert suggestions.status_code == 200
        assert suggestions.json()["suggestions"]

        updated = client.post(
            "/update_resume",
            json={
                "resume_text": "Skills\nPython\n",
                "accepted_suggestions": [],
                "accepted_skills": ["Docker"],
            },
        )
        assert updated.status_code == 200
        assert "Docker" in updated.json()["updated_resume_text"]

    def test_edit_resume(self, client):
        response = client.post(
            "/edit-resume",
            json={
                "resume_text": "SUMMARY\nBuilt web tools.\n",
                "instruction": 'Replace "web tools" with "internal dashboards".',
            },
        )
        assert response.status_code == 200
        assert "internal dashboards" in response.json()["updated_resume_text"]


class TestJobMatching:
    def test_jobs_are_ranked_with_transparent_components(self, client, sample_resume):
        response = client.post(
            "/job-match",
            json={
                "resume_text": sample_resume,
                "jobs": [
                    {
                        "id": "backend",
                        "title": "Backend Engineer",
                        "company": "Acme",
                        "text": "Required: Python, FastAPI, PostgreSQL.",
                    },
                    {
                        "id": "frontend",
                        "title": "Frontend Engineer",
                        "company": "Beta",
                        "text": "Required: Vue, CSS, TypeScript.",
                    },
                ],
            },
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["ranking"][0]["id"] == "backend"
        assert [item["rank"] for item in body["ranking"]] == [1, 2]
        assert body["best_match"]["id"] == "backend"
        assert body["ranking_explanations"]
        assert abs(sum(body["weights"].values()) - 1.0) < 1e-6
        assert body["disclaimer"]

    def test_custom_weights_are_normalised(self, client, sample_resume):
        response = client.post(
            "/job-match",
            json={
                "resume_text": sample_resume,
                "jobs": [{"title": "Backend", "text": "Required: Python."}],
                "weights": {"required_skill_coverage": 3, "experience_alignment": 1},
            },
        )
        assert response.status_code == 200
        weights = response.json()["weights"]
        assert abs(sum(weights.values()) - 1.0) < 1e-6
        assert weights["required_skill_coverage"] > weights["experience_alignment"]

    def test_job_match_handles_skills_outside_a_section(self, client):
        response = client.post(
            "/job-match",
            json={
                "resume_text": "Avery Chen\nPython developer\n\nExperience\n- Built APIs.\n",
                "jobs": [{"title": "Backend", "text": "Required: Python."}],
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["ranking"][0]["required_coverage"] >= 0

    def test_job_match_requires_resume_text(self, client):
        response = client.post(
            "/job-match",
            json={"resume_text": "", "jobs": [{"title": "Backend", "text": "Python"}]},
        )
        assert response.status_code == 422


class TestInterviewEndpoints:
    def test_question_generation_and_evaluation(self, client, sample_resume):
        generated = client.post(
            "/interview/questions",
            json={
                "role": "Backend Engineer",
                "required_skills": ["python", "docker"],
                "missing_skills": ["docker"],
                "resume_text": sample_resume,
            },
        )
        assert generated.status_code == 200, generated.text
        body = generated.json()
        assert body["questions"]
        assert any(item["source"] == "project" for item in body["questions"])
        assert body["disclaimer"]

        question = body["questions"][0]
        evaluated = client.post(
            "/interview/evaluate",
            json={
                "question": question["question"],
                "answer": (
                    "First I built a service with Python and measured results, therefore reducing latency. "
                    "The result was a 20% improvement and I learned to verify the change."
                ),
                "expected_concepts": question["expected_concepts"],
            },
        )
        assert evaluated.status_code == 200, evaluated.text
        assert 0 <= evaluated.json()["score"] <= 100
        assert evaluated.json()["feedback"]

    def test_interview_tips(self, client):
        response = client.get("/interview_tips?role=Backend")
        assert response.status_code == 200
        assert response.json()["questions"]
