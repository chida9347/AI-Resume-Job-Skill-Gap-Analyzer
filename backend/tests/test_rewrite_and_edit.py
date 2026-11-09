"""Conservative rewriting and deterministic resume editing."""

from __future__ import annotations

from services.resume_edit_service import edit_resume
from services.rewrite_service import rewrite_resume


class TestRuleBasedRewrite:
    def test_improves_weak_opening_without_inventing_metrics(self):
        resume = "EXPERIENCE\n- Worked on Python APIs.\nEDUCATION\nBachelor of Science\n"
        result = rewrite_resume(resume, "Python engineer with FastAPI experience.")
        assert result["method"] == "rule-based"
        assert "Contributed to Python APIs [add a verified outcome metric]" in result["rewritten"]
        assert "EDUCATION\nBachelor of Science" in result["rewritten"]
        assert "20%" not in result["rewritten"]
        assert result["ai_available"] is False
        assert "No employment history" in result["fabrication_notice"]

    def test_leaves_other_sections_unchanged(self):
        resume = (
            "SUMMARY\n- Worked on Python tools.\n"
            "EXPERIENCE\n- Worked on SQL reports, improving turnaround by 15%.\n"
        )
        result = rewrite_resume(resume, "Python and SQL experience required.")
        assert "SUMMARY\n- Worked on Python tools." in result["rewritten"]
        assert "Contributed to SQL reports, improving turnaround by 15%." in result["rewritten"]

    def test_formats_plain_experience_lines(self):
        resume = "EXPERIENCE\nBuilt Python APIs for internal tools.\nEDUCATION\nBachelor of Science\n"
        result = rewrite_resume(resume, "Python API engineer.")
        assert result["rewritten"].startswith("EXPERIENCE\n- Built Python APIs")
        assert "[add a verified outcome metric]" in result["rewritten"]

    def test_suggestions_require_approval(self):
        resume = "EXPERIENCE\n- Worked on Python APIs.\n"
        result = rewrite_resume(resume, "Python engineer.")
        assert result["suggestions"]
        assert all(item["requires_approval"] for item in result["suggestions"])
        assert all(item["original"] and item["suggestion"] for item in result["suggestions"])

    def test_consent_is_required_when_openai_is_enabled(self, monkeypatch):
        from config import get_settings

        settings = get_settings()
        monkeypatch.setattr(settings, "enable_openai_rewriter", True)
        monkeypatch.setattr(settings, "openai_api_key", "test-key")
        monkeypatch.setattr(settings, "openai_consent_default", False)
        result = rewrite_resume("EXPERIENCE\n- Worked on APIs.\n", "Backend role", ai_consent=False)
        # No network call is made without consent; the local path is used.
        assert result["method"] == "rule-based"
        assert result["ai_available"] is True
        assert result["ai_consent_required"] is True


class TestResumeChatEditing:
    def test_literal_replacement(self):
        result = edit_resume(
            "SUMMARY\nBuilt web tools.\n",
            'Replace "web tools" with "internal dashboards".',
        )
        assert result["updated_resume_text"] == "SUMMARY\nBuilt internal dashboards.\n"
        assert result["changed"] is True
        assert result["method"] == "local"

    def test_adds_supplied_text_under_existing_section(self):
        result = edit_resume(
            "SUMMARY\nDeveloper.\nEXPERIENCE\nBuilt APIs.\n",
            'Add "Used weekly by the support team." to Experience.',
        )
        assert "EXPERIENCE\nUsed weekly by the support team.\nBuilt APIs." in result["updated_resume_text"]
        assert result["changed"] is True

    def test_unsupported_request_does_not_mutate_resume(self):
        resume = "SUMMARY\nDeveloper.\n"
        result = edit_resume(
            resume,
            "Make me a senior engineer with five years of leadership experience.",
        )
        assert result["updated_resume_text"] == resume
        assert result["changed"] is False
        assert "No change was made" in result["reply"]

    def test_one_page_request_changes_layout_only(self):
        resume = "SUMMARY\nDeveloper with Python experience.\nEXPERIENCE\nBuilt useful tools.\n"
        result = edit_resume(resume, "Please make this resume fit on only one page.")
        assert result["updated_resume_text"] == resume
        assert result["fit_to_one_page"] is True
        assert "no resume content removed" in result["change_summary"].lower()

    def test_remove_quoted_text(self):
        result = edit_resume(
            "SUMMARY\nDeveloper.\nSKILLS\nPython, Java\n",
            'Remove "Java".',
        )
        assert "Java" not in result["updated_resume_text"]
        assert result["changed"] is True
