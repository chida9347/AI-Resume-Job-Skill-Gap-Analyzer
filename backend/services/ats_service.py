"""Explainable resume-to-job alignment scoring.

The output is deliberately presented as an *estimate*. Every component reports
its weight, raw score, awarded points and a reason. Caps prevent a weak match
from displaying a misleading 95–100 score.
"""

from __future__ import annotations

import re
from collections import Counter

from services.analyzer import compare_resume_to_job, extract_skills
from services.job_service import analyze_job_description
from services.resume_structurer import extract_structured_resume
from services.skill_taxonomy import DISPLAY_NAMES, SKILLS, category_of
from services.text_utils import (
    ACTION_VERBS,
    METRIC_PATTERN,
    STOPWORDS,
    detect_sections,
    keywords,
    normalize_text,
)

_WEIGHTS = {
    "required_skill_coverage": 30,
    "preferred_skill_coverage": 10,
    "keyword_relevance": 15,
    "section_completeness": 15,
    "experience_relevance": 10,
    "education_relevance": 5,
    "project_relevance": 10,
    "formatting_readability": 5,
}

_LABELS = {
    "required_skill_coverage": "Required skill coverage",
    "preferred_skill_coverage": "Preferred skill coverage",
    "keyword_relevance": "Job keyword relevance",
    "section_completeness": "Resume section completeness",
    "experience_relevance": "Relevant experience",
    "education_relevance": "Education relevance",
    "project_relevance": "Project relevance",
    "formatting_readability": "Formatting and readability",
}

_GENERIC_KEYWORDS = {
    "ability", "applicant", "candidate", "company", "culture", "demonstrated", "environment",
    "excellent", "experience", "familiarity", "fast", "global", "great", "including",
    "industry", "knowledge", "looking", "opportunity", "preferred", "products", "required",
    "requirements", "responsibilities", "solutions", "strong", "success", "team", "teams",
    "technology", "tools", "using", "various", "work", "working", "world",
}

_EDUCATION_DEGREE = re.compile(
    r"\b(?:bachelor|master|ph\.?\s?d|doctorate|b\.?\s?tech|m\.?\s?tech|b\.?\s?e\.?|m\.?\s?e\.?|"
    r"b\.?\s?sc|m\.?\s?sc|mba|degree|diploma)\b",
    re.IGNORECASE,
)
_EXPERIENCE_DATE = re.compile(
    r"(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+)?"
    r"(?:19|20)\d{2}\s*(?:[-–—]|to)\s*(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+)?"
    r"(?:(?:19|20)\d{2}|present|current)",
    re.IGNORECASE,
)
_YEAR = re.compile(r"\b(19|20)\d{2}\b")


def _keyword_present(keyword: str, text: str) -> bool:
    aliases = SKILLS.get(keyword, [keyword])
    return any(
        re.search(r"(?<![A-Za-z0-9])" + re.escape(alias.strip()) + r"(?![A-Za-z0-9])", text, re.IGNORECASE)
        for alias in aliases
    )


def _job_keywords(job_description: str, job: dict) -> list[str]:
    """Specific, explainable keywords. Generic nouns are excluded."""
    skills = list(dict.fromkeys([*job["required_skills"], *job["preferred_skills"], *job["mentioned_skills"]]))
    generic = [
        token
        for token in keywords(job_description, limit=25)
        if len(token) >= 5
        and token not in STOPWORDS
        and token not in _GENERIC_KEYWORDS
        and token not in skills
    ]
    # Prefer words that occur more than once or look like technologies (contain a dot/slash).
    counts = Counter(re.findall(r"[A-Za-z][A-Za-z0-9+#./-]*", job_description.lower()))
    generic = [token for token in generic if counts[token] >= 2 or any(char in token for char in "./+#")][:10]
    return list(dict.fromkeys([*skills, *generic]))[:40]


def _section_scores(resume_text: str, structured: dict) -> dict[str, int]:
    sections = detect_sections(resume_text)
    presence = structured["section_presence"]
    skills = extract_skills(resume_text)
    has_education = bool(_EDUCATION_DEGREE.search(resume_text))
    contact = structured["contact"]

    project_signals = bool(re.search(r"\b(?:built|developed|designed|created|implemented)\b", resume_text, re.I))
    return {
        "skills": 100 if presence["skills"] else 70 if len(skills) >= 5 else 40 if skills else 0,
        "experience": 100 if presence["experience"] else 50 if _EXPERIENCE_DATE.search(resume_text) else 0,
        "education": 100 if presence["education"] else 60 if has_education else 0,
        "projects": 100 if presence["projects"] else 40 if project_signals else 0,
        "certifications": 100 if presence["certifications"] else 0,
        "contact": 100 if contact.get("email") and contact.get("phone") else 80 if contact.get("email") else 40 if contact.get("phone") else 0,
        "summary": 100 if presence["summary"] else 0,
        "sections_detected": len([key for key, value in presence.items() if value]),
        "total_lines": len([line for line in sections.get("header", {}).get("lines", []) if line.strip()]),
    }


def _section_component(section: dict[str, int]) -> int:
    weights = {
        "skills": 0.24,
        "experience": 0.28,
        "education": 0.18,
        "projects": 0.16,
        "contact": 0.10,
        "certifications": 0.04,
    }
    return round(sum(section[key] * weight for key, weight in weights.items()))


def _formatting_quality(resume_text: str, structured: dict) -> tuple[int, list[str]]:
    score = 100
    notes: list[str] = []
    words = resume_text.split()
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    bullets = sum(1 for line in lines if re.match(r"^\s*(?:[-*+•·]|\d+[.)])\s+", line))
    if len(words) < 75:
        score -= 20
        notes.append("The resume is very short; add detail to experience or projects.")
    if len(words) > 12_000:
        score -= 15
        notes.append("The resume is unusually long; tighten it to the most relevant evidence.")
    if len(lines) < 4:
        score -= 15
        notes.append("Very few text lines were detected.")
    if sum(len(line) > 240 for line in lines) > 2:
        score -= 15
        notes.append("Several lines are very long; use concise bullets.")
    if lines and max(Counter(line.lower() for line in lines).values()) > 2:
        score -= 10
        notes.append("Repeated lines were detected.")
    if bullets == 0 and len(words) > 100:
        score -= 10
        notes.append("No bullet points were detected; bullets improve scanability.")
    if not structured["contact"].get("email"):
        score -= 10
        notes.append("No email address was detected in the resume.")
    if re.search(r"[^\x00-\x7F]", resume_text) and re.search(r"[\u2500-\u257F]", resume_text):
        score -= 5
        notes.append("Box-drawing characters were detected; they can confuse parsers.")
    return max(0, min(100, score)), notes


def _experience_relevance(resume_text: str, job: dict, structured: dict) -> tuple[int, str]:
    required_years = job["experience"].get("min_years")
    dates = _EXPERIENCE_DATE.findall(resume_text)
    resume_years = 0
    for span in dates:
        years = [int(value) for value in _YEAR.findall(span)]
        if len(years) >= 2:
            resume_years += max(0, years[-1] - years[0])
        elif years and re.search(r"present|current", span, re.I):
            from datetime import datetime

            resume_years += max(0, datetime.now().year - years[0])
    has_experience = bool(structured["experience"]) or bool(dates)
    if required_years is not None:
        if resume_years >= required_years:
            return 100, f"About {resume_years} year(s) of dated experience meets the {required_years}-year requirement."
        if resume_years >= max(0, required_years - 1):
            return 70, f"About {resume_years} year(s) of dated experience is close to the {required_years}-year requirement."
        if has_experience:
            return 45, f"Experience is present but dated evidence ({resume_years} year(s)) is below the {required_years}-year request."
        return 20, f"No dated experience was found; the role asks for {required_years}+ year(s)."
    if has_experience:
        if METRIC_PATTERN.search("\n".join(str(item) for item in structured["experience"])):
            return 100, "Experience is present and includes measurable outcomes."
        return 80, "Experience is present; add verified outcomes to strengthen it."
    return 30, "No clearly structured experience section was detected."


def _education_relevance(resume_text: str, job: dict, structured: dict) -> tuple[int, str]:
    required = job["education"]["required"]
    has_degree = bool(_EDUCATION_DEGREE.search(resume_text))
    if required:
        if has_degree:
            return 100, "A degree or diploma is present and the role requests one."
        if structured["education"]:
            return 65, "Education is present but no degree keyword was detected."
        return 20, "The role requests an educational qualification that was not found."
    if structured["education"] or has_degree:
        return 100, "Education information is present; the posting does not make a degree mandatory."
    return 70, "No education section was detected, but the posting does not require one."


def _project_relevance(resume_text: str, job: dict, structured: dict) -> tuple[int, str]:
    projects = structured["projects"]
    if not projects:
        return 20, "No projects section was detected."
    required = set(job["required_skills"])
    if not required:
        return 75, "Projects are present; no mandatory skills were detected to compare against."
    overlap = set()
    for project in projects:
        overlap.update(set(project.get("technologies", [])) & required)
    if overlap:
        names = ", ".join(DISPLAY_NAMES.get(skill, skill) for skill in sorted(overlap)[:5])
        return 100, f"Project evidence covers required skills: {names}."
    return 55, "Projects are present but do not explicitly use the role's required skills."


def _cap_score(score: int, comparison: dict, job: dict) -> tuple[int, list[dict]]:
    caps = []
    if not comparison["required_skills"]:
        caps.append({"reason": "No mandatory skills were detected in the posting.", "max": 90})
    else:
        if comparison["missing_required"]:
            caps.append(
                {
                    "reason": f"{len(comparison['missing_required'])} required skill(s) are not evidenced.",
                    "max": 92,
                }
            )
        if comparison["required_coverage"] < 70:
            caps.append({"reason": "Required skill coverage is below 70%.", "max": 82})
        strong = len(comparison["strong_skills"])
        if comparison["required_skills"] and strong / len(comparison["required_skills"]) < 0.5:
            caps.append({"reason": "Fewer than half of required skills have strong evidence.", "max": 90})
    caps.append({"reason": "Alignment scores are estimates, never a guaranteed employer score.", "max": 97})
    final = min(score, *(cap["max"] for cap in caps))
    return final, caps


def score_resume(
    resume_text: str,
    job_description: str,
    *,
    resume_skills: list[str] | None = None,
    job: dict | None = None,
    comparison: dict | None = None,
    structured: dict | None = None,
) -> dict:
    resume_text = normalize_text(resume_text)
    job_description = normalize_text(job_description)
    structured = structured or extract_structured_resume(resume_text)
    resume_skills = resume_skills or extract_skills(resume_text)
    job = job or analyze_job_description(job_description)
    comparison = comparison or compare_resume_to_job(
        resume_text,
        resume_skills,
        job["required_skills"],
        job["preferred_skills"],
        resume_confidence=structured["confidence"],
    )

    job_keywords = _job_keywords(job_description, job)
    matched_keywords = [keyword for keyword in job_keywords if _keyword_present(keyword, resume_text)]
    missing_keywords = [keyword for keyword in job_keywords if keyword not in matched_keywords]
    keyword_match = round(len(matched_keywords) / len(job_keywords) * 100) if job_keywords else 0

    sections = _section_scores(resume_text, structured)
    section_component = _section_component(sections)
    formatting, formatting_notes = _formatting_quality(resume_text, structured)
    experience_score, experience_reason = _experience_relevance(resume_text, job, structured)
    education_score, education_reason = _education_relevance(resume_text, job, structured)
    project_score, project_reason = _project_relevance(resume_text, job, structured)

    raw_scores = {
        "required_skill_coverage": comparison["required_coverage"],
        "preferred_skill_coverage": comparison["preferred_coverage"] if job["preferred_skills"] else 100,
        "keyword_relevance": keyword_match,
        "section_completeness": section_component,
        "experience_relevance": experience_score,
        "education_relevance": education_score,
        "project_relevance": project_score,
        "formatting_readability": formatting,
    }

    # If the posting has no preferred skills, do not penalise the candidate.
    weights = dict(_WEIGHTS)
    if not job["preferred_skills"]:
        weights["keyword_relevance"] += weights.pop("preferred_skill_coverage")
    if not job["required_skills"]:
        weights["keyword_relevance"] += weights.pop("required_skill_coverage")

    total_weight = sum(weights.values())
    breakdown = []
    awarded = 0.0
    for component, weight in weights.items():
        score = max(0, min(100, int(raw_scores[component])))
        points = round(score / 100 * weight, 1)
        awarded += points
        explanation = {
            "required_skill_coverage": (
                f"{len(comparison['matched_required'])} of {len(comparison['required_skills'])} required skills are evidenced "
                f"({comparison['required_coverage']}% weighted coverage)."
            ),
            "preferred_skill_coverage": (
                f"{len(comparison['matched_preferred'])} of {len(comparison['preferred_skills'])} preferred skills are evidenced."
            ),
            "keyword_relevance": f"{len(matched_keywords)} of {len(job_keywords)} specific job keywords were found.",
            "section_completeness": (
                f"Detected sections: {', '.join(key for key, value in structured['section_presence'].items() if value) or 'none'}."
            ),
            "experience_relevance": experience_reason,
            "education_relevance": education_reason,
            "project_relevance": project_reason,
            "formatting_readability": (
                "Text structure is readable." if formatting >= 85 else " ".join(formatting_notes) or "Some formatting issues were detected."
            ),
        }[component]
        breakdown.append(
            {
                "component": component,
                "label": _LABELS[component],
                "weight": weight,
                "score": score,
                "points": points,
                "max_points": weight,
                "explanation": explanation,
            }
        )

    raw_score = round(awarded / total_weight * 100) if total_weight else 0
    ats_score, caps = _cap_score(raw_score, comparison, job)

    feedback: list[str] = []
    if comparison["missing_required"]:
        feedback.append(
            "Required skills not evidenced: "
            + ", ".join(DISPLAY_NAMES.get(skill, skill) for skill in comparison["missing_required"][:6])
            + ". Add them only if you can demonstrate them."
        )
    if comparison["partial_required"]:
        feedback.append(
            "Partially matched required skills: "
            + ", ".join(DISPLAY_NAMES.get(skill, skill) for skill in comparison["partial_required"][:6])
            + ". Strengthen the evidence or add a relevant project."
        )
    if comparison["missing_preferred"]:
        feedback.append(
            "Preferred skills not found: "
            + ", ".join(DISPLAY_NAMES.get(skill, skill) for skill in comparison["missing_preferred"][:5])
            + "."
        )
    if comparison["mentioned_skills"]:
        feedback.append(
            "Move listed-only skills into experience or project bullets: "
            + ", ".join(DISPLAY_NAMES.get(skill, skill) for skill in comparison["mentioned_skills"][:5])
            + "."
        )
    if sections["skills"] < 70:
        feedback.append("Add a clearly labelled skills section grouped by category.")
    if sections["experience"] < 70:
        feedback.append("Add a clearly labelled experience section with role, employer and dates.")
    elif not METRIC_PATTERN.search(resume_text):
        feedback.append("Experience bullets lack measurable outcomes; add verified scope or results where possible.")
    if sections["education"] < 70 and job["education"]["required"]:
        feedback.append("Add the education or qualification the posting asks for.")
    if sections["projects"] < 70:
        feedback.append("Add a projects section with the technologies used and your specific contribution.")
    if formatting < 80:
        feedback.append("Improve structure with concise bullets, consistent headings and shorter lines.")
    if missing_keywords:
        feedback.append(
            "Job words not found in the resume: "
            + ", ".join(DISPLAY_NAMES.get(item, item) for item in missing_keywords[:5])
            + "."
        )
    if not job_keywords:
        feedback.append("No relevant keywords could be identified from the job description.")
    if not feedback:
        feedback.append("No immediate alignment issues were detected; tailor the summary to the role.")

    return {
        "ats_score": ats_score,
        "estimated_alignment_score": ats_score,
        "keyword_match": keyword_match,
        "job_keywords": job_keywords,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "section_score": {
            "skills": sections["skills"],
            "experience": sections["experience"],
            "education": sections["education"],
            "projects": sections["projects"],
            "certifications": sections["certifications"],
            "contact": sections["contact"],
        },
        "formatting_quality": formatting,
        "feedback": feedback,
        "breakdown": breakdown,
        # Legacy compatibility: component -> awarded points. Capped totals are
        # explained separately in score_caps; this is not a second score.
        "score_breakdown": {item["component"]: round(item["points"]) for item in breakdown},
        "required_coverage": comparison["required_coverage"],
        "preferred_coverage": comparison["preferred_coverage"],
        "experience_alignment": experience_score,
        "education_relevance": education_score,
        "project_relevance": project_score,
        "score_caps": caps,
        "confidence": comparison["confidence"],
        "disclaimer": (
            "This is an estimated resume-to-job alignment score produced from your text. "
            "It is not the score produced by any employer's proprietary ATS and does not predict selection."
        ),
    }
