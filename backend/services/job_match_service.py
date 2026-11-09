"""Transparent multi-job compatibility ranking.

Compatibility is a weighted sum of five explicitly reported components. The
weights are configurable and are returned with the response so the ranking can
be audited. The score is an estimate of alignment with the text supplied by the
user; it is not an employer ATS score and does not predict selection.
"""

from __future__ import annotations

from services.analyzer import compare_resume_to_job, extract_skills
from services.ats_service import score_resume
from services.job_service import analyze_job_description
from services.resume_structurer import extract_structured_resume
from services.skill_taxonomy import DISPLAY_NAMES

DEFAULT_WEIGHTS: dict[str, float] = {
    "required_skill_coverage": 0.40,
    "preferred_skill_coverage": 0.10,
    "experience_alignment": 0.20,
    "project_evidence": 0.15,
    "education_alignment": 0.15,
}

COMPONENT_LABELS = {
    "required_skill_coverage": "Required skill coverage",
    "preferred_skill_coverage": "Preferred skill coverage",
    "experience_alignment": "Experience alignment",
    "project_evidence": "Project evidence",
    "education_alignment": "Education and eligibility alignment",
}


def _normalise_weights(weights: dict | None) -> dict[str, float]:
    merged = dict(DEFAULT_WEIGHTS)
    for key, value in (weights or {}).items():
        if key in merged:
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                continue
            if numeric >= 0:
                merged[key] = numeric
    total = sum(merged.values())
    if total <= 0:
        return dict(DEFAULT_WEIGHTS)
    # Normalise so the final score is always on a 0–100 scale.
    return {key: value / total for key, value in merged.items()}


def _score_one(job: dict, resume_text: str, resume_skills: list[str], structured: dict, weights: dict[str, float]) -> dict:
    text = str(job.get("text") or job.get("description") or "").strip()
    job_intel = analyze_job_description(text)
    comparison = compare_resume_to_job(
        resume_text,
        resume_skills,
        job_intel["required_skills"],
        job_intel["preferred_skills"],
        resume_confidence=structured["confidence"],
    )
    ats = score_resume(
        resume_text,
        text,
        resume_skills=resume_skills,
        job=job_intel,
        comparison=comparison,
        structured=structured,
    )

    components = {
        "required_skill_coverage": comparison["required_coverage"] if job_intel["required_skills"] else 100,
        "preferred_skill_coverage": comparison["preferred_coverage"] if job_intel["preferred_skills"] else 100,
        "experience_alignment": ats["experience_alignment"],
        "project_evidence": ats["project_relevance"],
        "education_alignment": ats["education_relevance"],
    }
    compatibility = round(sum(components[key] * weight for key, weight in weights.items()))

    # Do not let a posting with no mandatory skills display a perfect match.
    if not job_intel["required_skills"]:
        compatibility = min(compatibility, 90)
    if comparison["missing_required"]:
        compatibility = min(compatibility, 92)

    matched = comparison["matched_required"]
    missing = comparison["missing_required"]
    partial = comparison["partial_required"]

    title = str(job.get("title") or "").strip() or job_intel["title"] or "Untitled role"
    company = str(job.get("company") or "").strip() or job_intel["company"]

    explanation_parts = [
        f"{len(matched)} of {len(job_intel['required_skills'])} required skills are evidenced"
        if job_intel["required_skills"]
        else "No mandatory skills were detected in this posting",
    ]
    if missing:
        explanation_parts.append(
            "gaps: " + ", ".join(DISPLAY_NAMES.get(skill, skill) for skill in missing[:4])
        )
    if partial:
        explanation_parts.append(
            "partial: " + ", ".join(DISPLAY_NAMES.get(skill, skill) for skill in partial[:3])
        )
    if ats["experience_alignment"] < 60:
        explanation_parts.append("experience evidence is below what the posting asks for")

    return {
        "id": job.get("id") or "",
        "title": title,
        "company": company,
        "compatibility_score": compatibility,
        "ats_score": ats["ats_score"],
        "required_coverage": comparison["required_coverage"],
        "preferred_coverage": comparison["preferred_coverage"],
        "components": components,
        "component_labels": COMPONENT_LABELS,
        "weights": weights,
        "matched_required": matched,
        "missing_required": missing,
        "partial_required": partial,
        "matched_preferred": comparison["matched_preferred"],
        "missing_preferred": comparison["missing_preferred"],
        "skill_labels": comparison["skill_labels"],
        "top_gaps": [DISPLAY_NAMES.get(skill, skill) for skill in missing[:6]],
        "explanation": "; ".join(explanation_parts) + ".",
        "job": {
            "required_skills": job_intel["required_skills"],
            "preferred_skills": job_intel["preferred_skills"],
            "experience": job_intel["experience"],
            "education": job_intel["education"],
            "confidence": job_intel["confidence"],
            "warnings": job_intel["warnings"],
        },
        "confidence": min(comparison["confidence"], job_intel["confidence"] or 100),
        "score_caps": ats["score_caps"],
        "disclaimer": ats["disclaimer"],
    }


def _rank_explanation(ranked: list[dict]) -> list[dict]:
    """Explain each adjacent ranking difference using the component scores."""
    notes: list[dict] = []
    for index in range(len(ranked) - 1):
        higher, lower = ranked[index], ranked[index + 1]
        deltas = {
            key: higher["components"][key] - lower["components"][key]
            for key in higher["components"]
        }
        driver = max(deltas, key=lambda key: abs(deltas[key]))
        notes.append(
            {
                "higher": higher["id"] or higher["title"],
                "lower": lower["id"] or lower["title"],
                "difference": higher["compatibility_score"] - lower["compatibility_score"],
                "main_driver": COMPONENT_LABELS.get(driver, driver),
                "main_driver_delta": deltas[driver],
                "summary": (
                    f"{higher['title']} ranks above {lower['title']} mainly because "
                    f"{COMPONENT_LABELS.get(driver, driver).lower()} is "
                    f"{abs(deltas[driver])} point(s) "
                    f"{'higher' if deltas[driver] >= 0 else 'lower'}."
                ),
            }
        )
    return notes


def rank_jobs(
    resume_text: str,
    jobs: list[dict],
    *,
    resume_skills: list[str] | None = None,
    structured: dict | None = None,
    weights: dict | None = None,
) -> dict:
    resume_text = (resume_text or "").strip()
    if not resume_text:
        raise ValueError("Resume text is required to compare jobs.")
    resume_skills = resume_skills or extract_skills(resume_text)
    structured = structured or extract_structured_resume(resume_text)
    normalised_weights = _normalise_weights(weights)

    scored = [
        _score_one(job, resume_text, resume_skills, structured, normalised_weights)
        for job in jobs
        if str(job.get("text") or job.get("description") or "").strip()
    ]
    scored.sort(key=lambda item: (-item["compatibility_score"], -item["required_coverage"]))

    for position, item in enumerate(scored, start=1):
        item["rank"] = position

    best = scored[0] if scored else None
    return {
        "jobs": scored,
        "ranking": [
            {
                "rank": item["rank"],
                "id": item["id"],
                "title": item["title"],
                "company": item["company"],
                "compatibility_score": item["compatibility_score"],
                "required_coverage": item["required_coverage"],
                "top_gaps": item["top_gaps"],
            }
            for item in scored
        ],
        "ranking_explanations": _rank_explanation(scored),
        "best_match": best,
        "weights": normalised_weights,
        "component_labels": COMPONENT_LABELS,
        "method": "weighted-transparent-compatibility",
        "disclaimer": (
            "Compatibility is an estimate of how well the supplied resume text aligns with the "
            "supplied job text. It is not an employer's ATS score and does not guarantee selection."
        ),
    }
