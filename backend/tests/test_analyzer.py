"""Service-level tests for skill extraction, matching and evidence.

These tests intentionally avoid the network and any semantic model. Semantic
similarity is simulated with monkeypatch so its *partial-only* contract can be
verified without downloading a model.
"""

from __future__ import annotations

import pytest

from services.analyzer import (
    compare_resume_to_job,
    compare_skills,
    extract_skills,
    make_suggestions,
    update_resume,
)
from services.skill_taxonomy import extract_canonical_skills


class TestSkillExtraction:
    def test_aliases_resolve_to_canonical_names(self):
        skills = extract_skills("Built REST APIs in Python and React.js, deployed with PostgreSQL.")
        assert skills[:3] == ["python", "react", "rest apis"]
        assert "postgresql" in skills

    def test_short_alias_does_not_match_dotted_product_name(self):
        # "React.js" must not create a standalone JavaScript or TypeScript match.
        assert extract_canonical_skills("React.js") == ["react"]
        assert extract_canonical_skills("Node.js") == ["node.js"]

    def test_explicit_short_aliases_still_match(self):
        assert extract_canonical_skills("I use js and ts daily.") == ["javascript", "typescript"]

    def test_java_and_javascript_are_distinct(self):
        assert extract_canonical_skills("Java") == ["java"]
        assert extract_canonical_skills("JavaScript") == ["javascript"]
        assert "java" not in extract_canonical_skills("JavaScript")

    def test_distinct_products_are_not_collapsed(self):
        skills = extract_canonical_skills("Used MySQL, PostgreSQL, GitHub and Tailwind CSS.")
        assert {"mysql", "postgresql", "github", "tailwind css"} <= set(skills)
        # PostgreSQL and MySQL are products, not generic SQL.
        assert "sql" not in skills

    def test_extraction_is_deduplicated_and_ordered(self):
        skills = extract_skills("Python, python, PYTHON and FastAPI.")
        assert skills.count("python") == 1
        assert skills.index("python") < skills.index("fastapi")


class TestListComparison:
    def test_exact_match_and_percentage(self):
        result = compare_skills(["python", "sql"], ["python", "sql", "docker"])
        assert result["matched_skills"] == ["python", "sql"]
        assert result["missing_skills"] == ["docker"]
        assert result["similarity_score"] == 67
        assert result["ats_score"] == 67

    def test_empty_job_skill_list_scores_zero(self):
        result = compare_skills(["python"], [])
        assert result["matched_skills"] == []
        assert result["missing_skills"] == []
        assert result["similarity_score"] == 0

    def test_implication_counts_as_match(self):
        # PostgreSQL is defensible evidence of SQL, unlike a merely related tool.
        result = compare_skills(["postgresql"], ["sql"])
        assert result["matched_skills"] == ["sql"]
        assert result["missing_skills"] == []

    def test_related_skill_is_partial_not_matched(self):
        result = compare_skills(["postgresql"], ["mysql"])
        assert "mysql" not in result["matched_skills"]
        assert "mysql" in result["partial_skills"]
        assert result["similarity_score"] == 0

    def test_preferred_skills_reported_separately(self):
        result = compare_skills(["python", "docker"], ["python"], ["docker", "aws"])
        assert result["matched_preferred_skills"] == ["docker"]
        assert result["missing_preferred_skills"] == ["aws"]
        assert result["matched_preferred"] == ["docker"]
        assert result["missing_preferred"] == ["aws"]


class TestEvidenceAwareComparison:
    def test_skill_demonstrated_in_experience_is_strong(self, sample_resume):
        result = compare_resume_to_job(
            sample_resume,
            ["python", "fastapi", "postgresql"],
            ["python"],
        )
        assert result["explanations"][0]["status"] == "strong"
        assert result["required_coverage"] == 100

    def test_listed_only_skill_is_mentioned(self):
        resume = "Avery Chen\nSkills\nDocker, Python\nExperience\n- Built APIs in Python.\n"
        result = compare_resume_to_job(resume, ["python", "docker"], ["docker"])
        status = {item["skill"]: item["status"] for item in result["explanations"]}
        assert status["docker"] == "mentioned"
        assert result["required_coverage"] == 60

    def test_implied_skill_is_credited_but_labelled(self):
        resume = "Avery Chen\nSkills\nPostgreSQL\nExperience\n- Built a service with PostgreSQL.\n"
        result = compare_resume_to_job(resume, ["postgresql"], ["sql"])
        explanation = result["explanations"][0]
        assert explanation["status"] == "implied"
        assert result["matched_required"] == ["sql"]

    def test_semantic_match_is_partial_and_never_proven(self, sample_resume, monkeypatch):
        monkeypatch.setattr(
            "services.analyzer._semantic_scores",
            lambda missing, resume: {"docker": 0.91},
        )
        result = compare_resume_to_job(sample_resume, ["python"], ["docker"])
        explanation = result["explanations"][0]
        assert explanation["status"] == "partial"
        assert result["matched_required"] == []
        assert result["partial_required"] == ["docker"]
        assert result["required_coverage"] == 30

    def test_missing_skill_has_no_credit(self, sample_resume):
        result = compare_resume_to_job(sample_resume, ["python"], ["docker"])
        assert result["explanations"][0]["status"] == "missing"
        assert result["required_coverage"] == 0
        assert "cannot" in result["disclaimer"].lower() or "not an employer" in result["disclaimer"].lower()


class TestResumeUpdates:
    def test_accepted_suggestions_are_review_notes_not_claims(self):
        result = update_resume("Existing experience", ["Review project work for Python examples"])
        assert result.startswith("Existing experience\n\nNOTES TO REVIEW\n")
        assert "Review project work for Python examples" in result

    def test_confirmed_skills_are_added_to_existing_skills_section(self):
        resume = "Avery Chen\nSkills\nPython, SQL\nExperience\nBuilt services."
        result = update_resume(resume, [], ["Kubernetes", "testing"])
        assert "Additional skills: Kubernetes, Testing" in result
        assert result.count("Kubernetes") == 1

    def test_confirmed_skills_do_not_match_substrings(self):
        result = update_resume("Avery Chen\nJavaScript developer", [], ["Java"])
        assert result.startswith("Skills\nJava\n\nAvery Chen")

    def test_confirmed_skill_deduplication(self):
        resume = "Skills: Python, Docker\nExperience\nBuilt tools."
        result = update_resume(resume, ["Add measurable outcomes"], ["Docker", "Kubernetes"])
        assert result.count("Docker") == 1
        assert "Skills: Python, Docker, Kubernetes" in result
        assert "NOTES TO REVIEW\n- Add measurable outcomes" in result

    def test_suggestions_require_confirmation_and_have_stable_ids(self):
        suggestions = make_suggestions(["docker"], "Avery Chen\nExperience\nBuilt things.")
        assert suggestions
        assert all(item["accepted"] is False for item in suggestions)
        ids = [item["id"] for item in suggestions]
        assert len(ids) == len(set(ids))


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Python and FastAPI", ["python", "fastapi"]),
        ("C++ and C#", ["c++", "c#"]),
        ("REST APIs", ["rest apis"]),
    ],
)
def test_extraction_smoke(text, expected):
    assert set(expected) <= set(extract_skills(text))
