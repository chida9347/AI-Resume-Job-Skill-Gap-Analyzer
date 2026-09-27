import unittest
from unittest.mock import patch

from services.analyzer import compare_skills, extract_skills, update_resume
from services.ats_service import score_resume
from services.learning_path_service import generate_learning_paths
from services.rewrite_service import rewrite_resume


class AnalyzerTests(unittest.TestCase):
    def test_extracts_canonical_skills_from_aliases(self):
        self.assertEqual(
            extract_skills("Built REST APIs in Python and React.js, deployed with PostgreSQL."),
            ["python", "react", "sql", "rest apis"],
        )

    @patch("services.analyzer._semantic_pairs", return_value=set())
    def test_compares_required_skills_and_calculates_percentage(self, _semantic_pairs):
        result = compare_skills(["python", "sql"], ["python", "sql", "docker"])

        self.assertEqual(result["matched_skills"], ["python", "sql"])
        self.assertEqual(result["missing_skills"], ["docker"])
        self.assertEqual(result["similarity_score"], 67)
        self.assertEqual(result["ats_score"], 67)

    def test_empty_job_skill_list_has_zero_score(self):
        result = compare_skills(["python"], [])

        self.assertEqual(result["matched_skills"], [])
        self.assertEqual(result["missing_skills"], [])
        self.assertEqual(result["similarity_score"], 0)

    def test_accepted_suggestions_are_review_notes_not_claims(self):
        result = update_resume("Existing experience", ["Review project work for Python examples"])

        self.assertTrue(result.startswith("Existing experience\n\nNOTES TO REVIEW\n"))
        self.assertIn("Review project work for Python examples", result)

    def test_confirmed_skills_are_added_to_existing_skills_section(self):
        resume = "Avery Chen\nSkills\nPython, SQL\nExperience\nBuilt services."
        result = update_resume(resume, [], ["Kubernetes", "testing"])

        self.assertIn("Skills\nPython, SQL\nAdditional skills: Kubernetes, Testing\nExperience", result)
        self.assertEqual(result.count("Kubernetes"), 1)

    def test_confirmed_skills_create_section_and_do_not_match_substrings(self):
        result = update_resume("Avery Chen\nJavaScript developer", [], ["Java"])

        self.assertTrue(result.startswith("Skills\nJava\n\nAvery Chen"))
        self.assertNotIn("JavaScript developer\nJava", result)

    def test_confirmed_skill_deduplication_and_review_notes_are_separate(self):
        resume = "Skills: Python, Docker\nExperience\nBuilt tools."
        result = update_resume(resume, ["Add measurable outcomes"], ["Docker", "Kubernetes"])

        self.assertIn("Skills: Python, Docker, Kubernetes", result)
        self.assertEqual(result.count("Docker"), 1)
        self.assertIn("NOTES TO REVIEW\n- Add measurable outcomes", result)

    def test_ats_score_returns_bounded_keyword_and_section_scores(self):
        resume = """Skills
Python FastAPI
Experience
Built APIs and improved response time by 20%.
Education
Bachelor of Science in Computer Science
"""
        result = score_resume(resume, "Seeking Python FastAPI Docker Kubernetes engineers.")

        self.assertEqual(result["matched_keywords"][:2], ["python", "fastapi"])
        self.assertIn("docker", result["missing_keywords"])
        self.assertIn("kubernetes", result["missing_keywords"])
        self.assertEqual(result["section_score"], {"skills": 100, "experience": 100, "education": 100})
        self.assertGreaterEqual(result["ats_score"], 0)
        self.assertLessEqual(result["ats_score"], 100)

    def test_ats_score_reports_empty_keyword_extraction(self):
        result = score_resume("Skills\nPython", "and or the with from")

        self.assertEqual(result["keyword_match"], 0)
        self.assertIn("No relevant keywords could be identified from the job description.", result["feedback"])

    def test_learning_path_has_actionable_roadmap_project_and_duration(self):
        paths = generate_learning_paths(["Docker"])

        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0]["skill"], "Docker")
        self.assertEqual(len(paths[0]["roadmap"]), 4)
        self.assertIn("Compose", paths[0]["project"])
        self.assertEqual(paths[0]["duration"], "5 days")

    def test_learning_path_deduplicates_and_supports_unknown_skills(self):
        paths = generate_learning_paths(["Custom tool", " custom TOOL "])

        self.assertEqual(len(paths), 1)
        self.assertEqual(len(paths[0]["roadmap"]), 4)
        self.assertIn("Custom tool", paths[0]["roadmap"][0])

    def test_rewriter_improves_experience_without_inventing_metrics(self):
        resume = """EXPERIENCE
- Worked on Python APIs.
EDUCATION
Bachelor of Science
"""
        result = rewrite_resume(resume, "Python engineer with FastAPI experience.")

        self.assertEqual(result["method"], "rule-based")
        self.assertIn("Contributed to Python APIs [add a verified outcome metric]", result["rewritten"])
        self.assertIn("EDUCATION\nBachelor of Science", result["rewritten"])
        self.assertNotIn("20%", result["rewritten"])
        self.assertTrue(any("python" in change.lower() for change in result["changes"]))

    def test_rewriter_leaves_non_experience_sections_unchanged(self):
        resume = """SUMMARY
- Worked on Python tools.
EXPERIENCE
- Worked on SQL reports, improving turnaround by 15%.
"""
        result = rewrite_resume(resume, "Python and SQL experience required.")

        self.assertIn("SUMMARY\n- Worked on Python tools.", result["rewritten"])
        self.assertIn("EXPERIENCE\n- Contributed to SQL reports, improving turnaround by 15%.", result["rewritten"])

    def test_rewriter_formats_plain_experience_lines_and_prompts_for_verified_metric(self):
        resume = """EXPERIENCE
Built Python APIs for internal tools.
EDUCATION
Bachelor of Science
"""
        result = rewrite_resume(resume, "Python API engineer.")

        self.assertNotEqual(result["rewritten"], result["original"])
        self.assertIn("- Built Python APIs for internal tools [add a verified outcome metric].", result["rewritten"])
        self.assertIn("EDUCATION\nBachelor of Science", result["rewritten"])


if __name__ == "__main__":
    unittest.main()