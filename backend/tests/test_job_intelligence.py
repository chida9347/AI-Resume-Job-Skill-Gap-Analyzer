"""Job-description intelligence: requirement cues, seniority and education."""

from __future__ import annotations

from services.job_service import analyze_job_description


class TestRequirementClassification:
    def test_inline_required_and_preferred_on_one_line(self):
        result = analyze_job_description("Required: Python and FastAPI. Preferred: Docker.")
        assert result["required_skills"] == ["python", "fastapi"]
        assert result["preferred_skills"] == ["docker"]
        assert result["technical_skills"] == ["python", "fastapi", "docker"]

    def test_section_headings_apply_to_following_lines(self):
        result = analyze_job_description(
            "Required qualifications:\nPython and SQL required.\n"
            "Preferred:\nDocker and AWS nice to have."
        )
        assert result["required_skills"] == ["python", "sql"]
        assert result["preferred_skills"] == ["docker", "aws"]

    def test_trailing_cue_governs_text_before_it(self):
        result = analyze_job_description("Python is required and Docker is preferred.")
        assert result["required_skills"] == ["python"]
        assert result["preferred_skills"] == ["docker"]

    def test_responsibility_prose_is_mentioned_not_required(self):
        result = analyze_job_description(
            "About the role\nYou will work with Python and Docker on internal tools."
        )
        assert result["required_skills"] == []
        assert {"python", "docker"} <= set(result["mentioned_skills"])

    def test_required_wins_when_skill_appears_in_both_contexts(self):
        result = analyze_job_description(
            "Preferred: Python.\nRequirements\n- Python required."
        )
        assert result["required_skills"] == ["python"]
        assert "python" not in result["preferred_skills"]

    def test_title_skills_are_mentioned_not_automatically_required(self):
        result = analyze_job_description("Senior React Developer\nWe build friendly products.")
        assert "react" in result["mentioned_skills"]
        assert "react" not in result["required_skills"]


class TestJobMetadata:
    def test_extracts_experience_years(self):
        result = analyze_job_description("Requirements\n- 3+ years of experience with Python.")
        assert result["experience"]["min_years"] == 3
        assert "python" in result["required_skills"]

    def test_extracts_degree_requirement(self):
        result = analyze_job_description("Requirements\n- Bachelor degree required.")
        assert result["education"]["required"] is True

    def test_confidence_reflects_extraction_quality(self):
        strong = analyze_job_description(
            "Backend Engineer\nRequired: Python, FastAPI, PostgreSQL, Docker.\n"
            "3+ years of experience. Bachelor degree required."
        )
        weak = analyze_job_description("We are a friendly company.")
        assert strong["confidence"] > weak["confidence"]
        assert weak["warnings"]

    def test_empty_job_description_is_safe(self):
        result = analyze_job_description("")
        assert result["required_skills"] == []
        assert result["preferred_skills"] == []
        assert result["technical_skills"] == []
        assert result["confidence"] == 0
