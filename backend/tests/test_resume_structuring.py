"""Structured resume extraction: present information only, no fabrication."""

from __future__ import annotations

from services.resume_structurer import extract_structured_resume
from services.text_utils import detect_sections, section_key_for_heading


class TestSectionDetection:
    def test_common_headings_are_recognised(self):
        assert section_key_for_heading("Skills")[0] == "skills"
        assert section_key_for_heading("Work Experience")[0] == "experience"
        assert section_key_for_heading("Education")[0] == "education"
        assert section_key_for_heading("Projects")[0] == "projects"

    def test_inline_heading_keeps_inline_text(self):
        key, inline = section_key_for_heading("Experience: 5 years")
        assert key == "experience"
        assert inline == "5 years"

    def test_prose_and_names_are_not_headings(self):
        assert section_key_for_heading("Avery Chen") is None
        assert section_key_for_heading("Built REST APIs in Python.") is None

    def test_detect_sections_groups_lines(self):
        text = (
            "Avery Chen\n"
            "avery@example.com\n"
            "Skills\nPython, FastAPI\n"
            "Experience\n- Built APIs.\n"
            "Education\nBachelor of Science\n"
        )
        result = detect_sections(text)
        assert result["sections"]["skills"]["lines"] == ["Python, FastAPI"]
        assert result["sections"]["experience"]["lines"] == ["- Built APIs."]
        assert "skills" in result["line_sections"]


class TestStructuredExtraction:
    def test_contact_skills_and_sections(self, sample_resume):
        result = extract_structured_resume(sample_resume)
        assert result["contact"]["name"] == "Avery Chen"
        assert result["contact"]["email"] == "avery@example.com"
        assert result["contact"]["phone"]
        assert {"python", "fastapi", "postgresql"} <= set(result["skills"]["all"])
        assert result["section_presence"]["skills"] is True
        assert result["section_presence"]["experience"] is True
        assert result["section_presence"]["certifications"] is False

    def test_projects_capture_technologies_and_metrics(self):
        text = (
            "Avery Chen\nProjects\nRoleprint\n"
            "- Built a FastAPI service with PostgreSQL and React, reducing latency by 30%.\n"
        )
        result = extract_structured_resume(text)
        project = result["projects"][0]
        assert project["title"] == "Roleprint"
        assert {"fastapi", "postgresql", "react"} <= set(project["technologies"])
        assert project["outcomes"]
        assert "30%" in project["outcomes"][0]

    def test_education_is_extracted_without_inventing_an_institution(self):
        result = extract_structured_resume(
            "Avery Chen\nEducation\nBachelor of Science in Computer Science\n"
        )
        entry = result["education"][0]
        assert "Bachelor" in entry["degree"]
        assert entry["institution"] == ""
        assert entry["gpa"] == ""

    def test_missing_sections_are_reported_not_invented(self):
        result = extract_structured_resume(
            "Avery Chen\navery@example.com\nSkills\nPython\nExperience\nBuilt APIs.\n"
        )
        assert "projects" in result["missing_information"]
        assert result["projects"] == []
        assert result["certifications"] == []

    def test_short_document_has_low_confidence_and_warning(self):
        result = extract_structured_resume("Avery Chen\nPython")
        assert result["confidence"] <= 35
        assert any("very short" in warning.lower() for warning in result["warnings"])

    def test_empty_text_is_safe(self):
        result = extract_structured_resume("")
        assert result["skills"]["all"] == []
        assert result["confidence"] == 0
        assert result["warnings"]

    def test_sections_are_counted_and_skills_grouped_by_category(self, sample_resume):
        result = extract_structured_resume(sample_resume)
        assert result["skills"]["total"] == len(result["skills"]["all"])
        assert result["skills"]["category_count"] == len(result["skills"]["by_category"])
        assert any(
            "Programming Languages" in category
            for category in result["skills"]["by_category"]
        )
