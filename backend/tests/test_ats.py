"""Explainable ATS scoring: bounded, capped and component-based."""

from __future__ import annotations

from services.ats_service import score_resume


class TestATSScoring:
    def test_score_is_bounded_and_never_a_perfect_claim(self, sample_resume, sample_job):
        result = score_resume(sample_resume, sample_job)
        assert 0 <= result["ats_score"] <= 100
        assert result["ats_score"] < 95
        assert result["score_caps"]
        assert any("estimate" in cap["reason"].lower() for cap in result["score_caps"])

    def test_every_component_is_explained(self, sample_resume, sample_job):
        result = score_resume(sample_resume, sample_job)
        components = {item["component"] for item in result["breakdown"]}
        assert components == {
            "required_skill_coverage",
            "preferred_skill_coverage",
            "keyword_relevance",
            "section_completeness",
            "experience_relevance",
            "education_relevance",
            "project_relevance",
            "formatting_readability",
        }
        for item in result["breakdown"]:
            assert item["label"]
            assert item["explanation"]
            assert item["weight"] >= 0
            assert 0 <= item["score"] <= 100

    def test_breakdown_totals_are_consistent_with_the_score(self, sample_resume, sample_job):
        result = score_resume(sample_resume, sample_job)
        total = sum(result["score_breakdown"].values())
        # Per-component rounding may differ from the raw total by a point or two,
        # and caps may lower the final value further.
        assert total >= result["ats_score"] - 3
        assert total <= 100

    def test_section_scores_are_reported(self, sample_resume, sample_job):
        result = score_resume(sample_resume, sample_job)
        assert result["section_score"]["skills"] == 100
        assert result["section_score"]["experience"] == 100
        assert result["section_score"]["education"] == 100
        assert result["section_score"]["projects"] == 100
        assert result["section_score"]["certifications"] == 0

    def test_missing_required_skill_is_capped_and_explained(self, sample_resume, sample_job):
        result = score_resume(sample_resume, sample_job)
        assert result["ats_score"] <= 92
        assert any("required skill" in cap["reason"].lower() for cap in result["score_caps"])
        assert any("docker" in feedback.lower() for feedback in result["feedback"])

    def test_job_without_required_skills_is_capped_below_perfect(self):
        resume = "Avery Chen\navery@example.com\nSkills\nPython\nExperience\nBuilt tools."
        result = score_resume(resume, "We are a friendly company building useful products.")
        assert result["ats_score"] <= 90
        assert any("no mandatory skills" in cap["reason"].lower() for cap in result["score_caps"])

    def test_keyword_extraction_handles_stopword_only_job(self):
        result = score_resume("Skills\nPython", "and or the with from")
        assert result["keyword_match"] == 0
        assert any(
            "No relevant keywords could be identified" in feedback
            for feedback in result["feedback"]
        )

    def test_matched_and_missing_keywords_are_disjoint(self, sample_resume, sample_job):
        result = score_resume(sample_resume, sample_job)
        assert set(result["matched_keywords"]).isdisjoint(result["missing_keywords"])
        assert "python" in result["matched_keywords"]
        assert "docker" in result["missing_keywords"]

    def test_short_resume_receives_formatting_feedback(self):
        result = score_resume("Python", "Required: Python, Docker.")
        assert result["formatting_quality"] < 100
        assert result["feedback"]

    def test_disclaimer_states_estimate(self, sample_resume, sample_job):
        result = score_resume(sample_resume, sample_job)
        assert "not the score produced by any employer" in result["disclaimer"]
        assert "does not predict selection" in result["disclaimer"]
