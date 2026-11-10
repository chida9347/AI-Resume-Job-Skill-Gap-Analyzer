"""Hybrid skill extraction, matching and resume-update services.

Matching layers:
1. exact canonical match
2. defensible implication (PostgreSQL -> SQL)
3. synonym match (handled by the taxonomy aliases during extraction)
4. semantic/related match, reported as *partial* only
5. evidence classification (strong / mentioned / missing)
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Iterable

from config import get_settings
from services.job_service import analyze_job_description
from services.resume_structurer import extract_structured_resume, skill_evidence
from services.skill_taxonomy import (
    DISPLAY_NAMES,
    SKILL_BY_NAME,
    SKILLS,
    category_of,
    extract_canonical_skills,
    find_occurrences,
    implied_skills,
    related_skills,
)
from services.text_utils import METRIC_PATTERN, detect_sections, normalize_text

__all__ = [
    "SKILLS",
    "analyze_all",
    "analyze_job_description",
    "compare_skills",
    "compare_resume_to_job",
    "extract_skills",
    "extract_skill_details",
    "interview_tips",
    "make_suggestions",
    "update_resume",
]

def _contains_phrase(text: str, phrase: str) -> bool:
    pattern = r"(?<![A-Za-z0-9])" + re.escape(phrase.strip()) + r"(?![A-Za-z0-9])"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def extract_skills(text: str) -> list[str]:
    """Return canonical skill identifiers in taxonomy order."""
    return extract_canonical_skills(normalize_text(text))


def extract_skill_details(text: str) -> list[dict]:
    occurrences = find_occurrences(text)
    by_skill: dict[str, list[dict]] = {}
    for item in occurrences:
        by_skill.setdefault(item["skill"], []).append(item)

    details = []
    for skill, items in by_skill.items():
        details.append(
            {
                "skill": skill,
                "display": DISPLAY_NAMES.get(skill, skill.title()),
                "category": category_of(skill),
                "mentions": len(items),
                "aliases": sorted({item["alias"] for item in items}),
                "surface_forms": sorted({item["surface"] for item in items}),
            }
        )
    details.sort(key=lambda item: (-item["mentions"], item["display"].lower()))
    return details


@lru_cache(maxsize=1)
def _embedding_model():
    settings = get_settings()
    if not settings.enable_semantic_matching:
        return None
    try:
        from sentence_transformers import SentenceTransformer

        # Local-only loading avoids unexpected downloads or network access.
        return SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
    except Exception:
        return None


def _semantic_scores(missing: Iterable[str], resume_skills: Iterable[str]) -> dict[str, float]:
    model = _embedding_model()
    if model is None:
        return {}
    try:
        from sentence_transformers import util

        missing_list = [DISPLAY_NAMES.get(item, item) for item in dict.fromkeys(missing)]
        resume_list = [DISPLAY_NAMES.get(item, item) for item in dict.fromkeys(resume_skills)]
        if not missing_list or not resume_list:
            return {}
        scores = util.cos_sim(model.encode(missing_list), model.encode(resume_list))
        result: dict[str, float] = {}
        for index, display in enumerate(missing_list):
            best = float(scores[index].max())
            if best >= 0.82:
                # map display back to canonical
                canonical = next(
                    (name for name, shown in DISPLAY_NAMES.items() if shown == display), display.lower()
                )
                result[canonical] = round(best, 3)
        return result
    except Exception:
        return {}


def _semantic_pairs(missing: Iterable[str], resume_skills: Iterable[str]) -> set[str]:
    """Backwards-compatible helper retained for tests and callers."""
    return set(_semantic_scores(missing, resume_skills))


def _dedupe(values: Iterable[str]) -> list[str]:
    cleaned = []
    seen = set()
    for value in values:
        item = str(value).strip().lower()
        if not item or item in seen or len(item) > 80:
            continue
        seen.add(item)
        cleaned.append(item)
    return cleaned


def _implied_match(required: str, resume_set: set[str]) -> str | None:
    for resume_skill in resume_set:
        if required in implied_skills(resume_skill):
            return resume_skill
    return None


def _related_match(required: str, resume_set: set[str]) -> str | None:
    for candidate in related_skills(required):
        if candidate in resume_set:
            return candidate
    for resume_skill in resume_set:
        if required in related_skills(resume_skill):
            return resume_skill
    return None


def _category_reason(skill: str) -> str:
    category = category_of(skill)
    reasons = {
        "Programming Languages": "Core language proficiency is usually a baseline requirement for this role.",
        "Frontend": "The role expects user-facing implementation work.",
        "Backend": "The role expects service or API development work.",
        "Databases": "The role expects data storage, querying or modelling work.",
        "Cloud & DevOps": "The role expects deployment, infrastructure or reliability work.",
        "Data & ML": "The role expects analytical or machine-learning work.",
        "Testing & Security": "The role expects quality, reliability or security practices.",
        "CS Fundamentals": "The role expects foundational computer-science knowledge.",
        "Soft Skills": "The posting explicitly asks for this way of working.",
        "Business & Product": "The role expects product or business context.",
        "Tools & Practices": "The role expects familiarity with this workflow or tool.",
    }
    return reasons.get(category, "The posting names this as relevant to the role.")


def _evidence_summary(skill: str, evidence: list[dict]) -> dict:
    if not evidence:
        return {"status": "missing", "strength": "none", "sections": [], "snippet": ""}
    strongest = next((item for item in evidence if item["strength"] == "strong"), evidence[0])
    return {
        "status": "present",
        "strength": strongest["strength"],
        "sections": sorted({item["section"] for item in evidence if item.get("section")}),
        "snippet": strongest["sentence"],
        "has_metric": any(item.get("has_metric") for item in evidence),
    }


def compare_skills(resume_skills: list[str], job_skills: list[str], preferred_skills: list[str] | None = None) -> dict:
    """Legacy list-only comparison. Rich evidence is unavailable without text."""
    preferred_skills = preferred_skills or []
    resume_list = _dedupe(resume_skills)
    resume_set = set(resume_list)
    required = _dedupe(job_skills)
    preferred = [skill for skill in _dedupe(preferred_skills) if skill not in required]

    matched = []
    implied: dict[str, str] = {}
    for skill in required:
        if skill in resume_set:
            matched.append(skill)
        else:
            source = _implied_match(skill, resume_set)
            if source:
                matched.append(skill)
                implied[skill] = source

    unmatched = [skill for skill in required if skill not in matched]
    partial: dict[str, dict] = {}
    for skill in unmatched:
        source = _related_match(skill, resume_set)
        if source:
            partial[skill] = {"reason": "related", "source": source, "similarity": None}
    for skill, score in _semantic_scores(
        [skill for skill in unmatched if skill not in partial], resume_set
    ).items():
        partial[skill] = {"reason": "semantic", "source": "", "similarity": score}

    missing = [skill for skill in unmatched if skill not in partial]

    matched_preferred = [skill for skill in preferred if skill in resume_set]
    missing_preferred = [skill for skill in preferred if skill not in resume_set]

    score = round(len(matched) / len(required) * 100) if required else 0
    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "partial_skills": list(partial),
        "similarity_score": score,
        "ats_score": score,
        "required_skills": required,
        "matched_required": matched,
        "missing_required": missing,
        "matched_preferred": matched_preferred,
        "missing_preferred": missing_preferred,
        # Legacy aliases retained for older clients.
        "matched_preferred_skills": matched_preferred,
        "missing_preferred_skills": missing_preferred,
        "required_coverage": score,
        "preferred_coverage": (
            round(len(matched_preferred) / len(preferred) * 100) if preferred else 0
        ),
        "explanations": [
            {
                "skill": skill,
                "status": "matched" if skill in matched else "partial" if skill in partial else "missing",
                "reason": (
                    f"Matched via {implied[skill]} which implies {skill}."
                    if skill in implied
                    else _category_reason(skill)
                ),
                "evidence": [],
            }
            for skill in required
        ],
        "skill_labels": {skill: DISPLAY_NAMES.get(skill, skill.title()) for skill in required},
        "evidence": {},
        "method": "exact+synonym+related",
        "confidence": 100 if required else 0,
        "disclaimer": "Keyword and taxonomy matching cannot prove that a skill was used in practice.",
    }


def compare_resume_to_job(
    resume_text: str,
    resume_skills: list[str],
    required_skills: list[str],
    preferred_skills: list[str] | None = None,
    *,
    resume_confidence: int = 100,
) -> dict:
    """Evidence-aware comparison used by the combined analysis endpoint."""
    preferred_skills = preferred_skills or []
    resume_set = {skill.lower() for skill in resume_skills}
    required = _dedupe(required_skills)
    preferred = [skill for skill in _dedupe(preferred_skills) if skill not in required]

    sections = detect_sections(resume_text)
    evidence_cache: dict[str, list[dict]] = {}

    def evidence_for(skill: str) -> list[dict]:
        if skill not in evidence_cache:
            evidence_cache[skill] = skill_evidence(resume_text, skill)
        return evidence_cache[skill]

    def classify(skill: str) -> dict:
        if skill in resume_set:
            evidence = evidence_for(skill)
            summary = _evidence_summary(skill, evidence)
            if summary["strength"] == "strong":
                return {
                    "status": "strong",
                    "credit": 1.0,
                    "evidence": evidence,
                    "reason": "Found in a demonstrated experience/project sentence.",
                }
            return {
                "status": "mentioned",
                "credit": 0.6,
                "evidence": evidence,
                "reason": "Mentioned in the resume, but not clearly tied to an experience or project outcome.",
            }
        source = _implied_match(skill, resume_set)
        if source:
            return {
                "status": "implied",
                "credit": 0.9,
                "evidence": evidence_for(source),
                "reason": f"Your {DISPLAY_NAMES.get(source, source)} experience implies {DISPLAY_NAMES.get(skill, skill)}.",
            }
        related = _related_match(skill, resume_set)
        if related:
            return {
                "status": "partial",
                "credit": 0.3,
                "evidence": evidence_for(related),
                "reason": f"Related skill found ({DISPLAY_NAMES.get(related, related)}); not the same as {DISPLAY_NAMES.get(skill, skill)}.",
            }
        return {"status": "missing", "credit": 0.0, "evidence": [], "reason": _category_reason(skill)}

    required_results = {skill: classify(skill) for skill in required}
    preferred_results = {skill: classify(skill) for skill in preferred}

    semantic = _semantic_scores(
        [skill for skill, result in required_results.items() if result["status"] == "missing"],
        resume_set,
    )
    for skill, score in semantic.items():
        required_results[skill] = {
            "status": "partial",
            "credit": 0.3,
            "evidence": [],
            "reason": f"Semantically related resume content was found (similarity {score:.2f}), but the skill is not explicit.",
        }

    matched_required = [skill for skill, result in required_results.items() if result["status"] in {"strong", "mentioned", "implied"}]
    partial_required = [skill for skill, result in required_results.items() if result["status"] == "partial"]
    missing_required = [skill for skill, result in required_results.items() if result["status"] == "missing"]
    matched_preferred = [skill for skill, result in preferred_results.items() if result["status"] in {"strong", "mentioned", "implied"}]
    partial_preferred = [skill for skill, result in preferred_results.items() if result["status"] == "partial"]
    missing_preferred = [skill for skill, result in preferred_results.items() if result["status"] == "missing"]

    required_credit = sum(result["credit"] for result in required_results.values())
    preferred_credit = sum(result["credit"] for result in preferred_results.values())
    required_coverage = round(required_credit / len(required) * 100) if required else 0
    preferred_coverage = round(preferred_credit / len(preferred) * 100) if preferred else 0

    # Strict presence score keeps the legacy semantics (used by the headline card).
    presence = len(matched_required) / len(required) * 100 if required else 0
    similarity = round(presence)

    explanations = []
    for skill in [*required, *preferred]:
        result = required_results.get(skill) or preferred_results.get(skill) or {}
        explanations.append(
            {
                "skill": skill,
                "display": DISPLAY_NAMES.get(skill, skill.title()),
                "category": category_of(skill),
                "requirement": "required" if skill in required else "preferred",
                "status": result.get("status", "missing"),
                "reason": result.get("reason", ""),
                "evidence": [
                    {
                        "section": item["section"],
                        "sentence": item["sentence"],
                        "strength": item["strength"],
                    }
                    for item in result.get("evidence", [])[:2]
                ],
            }
        )

    evidence_map = {
        skill: [
            {"section": item["section"], "sentence": item["sentence"], "strength": item["strength"]}
            for item in result["evidence"][:2]
        ]
        for skill, result in {**required_results, **preferred_results}.items()
        if result["evidence"]
    }

    strong_required = sum(1 for result in required_results.values() if result["status"] == "strong")
    confidence = resume_confidence
    if required and strong_required == 0:
        confidence = min(confidence, 70)

    return {
        # Legacy keys
        "matched_skills": matched_required,
        "missing_skills": missing_required,
        "similarity_score": similarity,
        "ats_score": similarity,
        # Rich keys
        "required_skills": required,
        "preferred_skills": preferred,
        "matched_required": matched_required,
        "missing_required": missing_required,
        "partial_required": partial_required,
        "matched_preferred": matched_preferred,
        "missing_preferred": missing_preferred,
        "partial_preferred": partial_preferred,
        "partial_skills": list(dict.fromkeys([*partial_required, *partial_preferred])),
        "required_coverage": required_coverage,
        "preferred_coverage": preferred_coverage,
        "strong_skills": [skill for skill, result in required_results.items() if result["status"] == "strong"],
        "mentioned_skills": [skill for skill, result in required_results.items() if result["status"] == "mentioned"],
        "explanations": explanations,
        "evidence": evidence_map,
        "skill_labels": {
            skill: DISPLAY_NAMES.get(skill, skill.title())
            for skill in [*required, *preferred]
        },
        "method": "exact+synonym+implication+related+evidence",
        "confidence": confidence,
        "disclaimer": (
            "This is an estimated resume-to-job alignment report based on the text you provided. "
            "It is not an employer's ATS score and cannot determine whether you will be selected."
        ),
    }


def make_suggestions(missing_skills: list[str], resume_text: str) -> list[dict]:
    suggestions: list[dict] = []
    text = normalize_text(resume_text or "")
    sections = detect_sections(text)
    existing = set(extract_skills(text))

    for skill in _dedupe(missing_skills)[:10]:
        suggestions.append(
            {
                "id": f"skill-{skill}",
                "skill": skill,
                "display": DISPLAY_NAMES.get(skill, skill.title()),
                "kind": "skill",
                "category": category_of(skill),
                "text": f"I have this skill; add {DISPLAY_NAMES.get(skill, skill.title())} to my resume Skills section.",
                "rationale": "Only confirm this if you can discuss or demonstrate it in an interview.",
                "accepted": False,
            }
        )

    # Mentioned-only skills deserve a stronger evidence suggestion.
    for skill in list(existing)[:20]:
        evidence = skill_evidence(text, skill)
        if evidence and all(item["strength"] == "mentioned" for item in evidence):
            suggestions.append(
                {
                    "id": f"evidence-{skill}",
                    "skill": skill,
                    "display": DISPLAY_NAMES.get(skill, skill.title()),
                    "kind": "review",
                    "category": category_of(skill),
                    "text": (
                        f"{DISPLAY_NAMES.get(skill, skill.title())} is listed but not clearly demonstrated. "
                        "Add a project or experience bullet describing what you built with it and the result."
                    ),
                    "rationale": "Evidence in context is more persuasive than a keyword list.",
                    "accepted": False,
                }
            )

    experience_text = "\n".join(
        [*sections["sections"].get("experience", {}).get("lines", [])]
    )
    if experience_text and not METRIC_PATTERN.search(experience_text):
        suggestions.append(
            {
                "id": "add-metrics",
                "skill": "Measurable outcomes",
                "display": "Measurable outcomes",
                "kind": "review",
                "category": "Resume quality",
                "text": "Add verified scope or outcome metrics to your strongest experience bullets (for example team size, latency, volume, time saved).",
                "rationale": "Specific, truthful outcomes are easier for a reader to evaluate.",
                "accepted": False,
            }
        )

    if not sections["sections"].get("projects"):
        suggestions.append(
            {
                "id": "add-projects",
                "skill": "Projects",
                "display": "Projects",
                "kind": "review",
                "category": "Resume structure",
                "text": "Add a Projects section with 1–2 relevant builds, the technologies used and your specific contribution.",
                "rationale": "Projects provide evidence when work experience is limited.",
                "accepted": False,
            }
        )

    if len(text.split()) < 180:
        suggestions.append(
            {
                "id": "add-detail",
                "skill": "More detail",
                "display": "More detail",
                "kind": "review",
                "category": "Resume quality",
                "text": "Add context, scope and measurable outcomes to your strongest experience or project.",
                "rationale": "Short resumes often omit the evidence a reviewer needs.",
                "accepted": False,
            }
        )

    # Stable de-duplication by id.
    return list({item["id"]: item for item in suggestions}.values())


_SKILLS_HEADING = re.compile(r"^\s*(?:technical\s+)?skills\s*:?\s*$", re.IGNORECASE)
_INLINE_SKILLS_HEADING = re.compile(r"^(\s*(?:technical\s+)?skills\s*:\s*)(.*)$", re.IGNORECASE)
_RESUME_SECTION_HEADING = re.compile(
    r"^\s*(?:summary|profile|objective|professional\s+)?(?:experience|employment\s+history|work\s+history|education|skills|technical\s+skills|projects?|certifications?|volunteer|awards?)\s*:?\s*$",
    re.IGNORECASE,
)
_SKILL_DISPLAY_NAMES = DISPLAY_NAMES


def _contains_skill_phrase(text: str, skill: str) -> bool:
    pattern = r"(?<![A-Za-z0-9])" + re.escape(skill.strip()) + r"(?![A-Za-z0-9])"
    return re.search(pattern, text, re.IGNORECASE) is not None


def _display_for(skill: str) -> str:
    cleaned = skill.strip()
    if not cleaned:
        return ""
    canonical = cleaned.casefold()
    if canonical in _SKILL_DISPLAY_NAMES:
        return _SKILL_DISPLAY_NAMES[canonical]
    return cleaned.title()


def _insert_confirmed_skills(resume_text: str, accepted_skills: list[str]) -> str:
    skills = list(
        dict.fromkeys(
            _display_for(skill)
            for skill in accepted_skills
            if skill.strip() and len(skill.strip()) <= 80 and not re.search(r"[\r\n]", skill)
        )
    )
    if not skills:
        return resume_text

    lines = resume_text.splitlines()
    for index, line in enumerate(lines):
        inline_match = _INLINE_SKILLS_HEADING.match(line)
        if inline_match:
            existing = inline_match.group(2)
            additions = [skill for skill in skills if not _contains_skill_phrase(existing, skill)]
            if additions:
                separator = ", " if existing.strip() else ""
                lines[index] = inline_match.group(1) + inline_match.group(2).rstrip() + separator + ", ".join(additions)
            return "\n".join(lines)

        if not _SKILLS_HEADING.match(line):
            continue

        next_section = next(
            (position for position in range(index + 1, len(lines)) if _RESUME_SECTION_HEADING.match(lines[position])),
            len(lines),
        )
        section_text = " ".join(lines[index + 1:next_section])
        additions = [skill for skill in skills if not _contains_skill_phrase(section_text, skill)]
        if additions:
            insertion = next_section
            while insertion > index + 1 and not lines[insertion - 1].strip():
                insertion -= 1
            lines.insert(insertion, "Additional skills: " + ", ".join(additions))
        return "\n".join(lines)

    additions = [skill for skill in skills if not _contains_skill_phrase(resume_text, skill)]
    if not additions:
        return resume_text
    section = "Skills\n" + ", ".join(additions)
    return section + "\n\n" + resume_text.lstrip()


def update_resume(
    resume_text: str,
    accepted_suggestions: list[str],
    accepted_skills: list[str] | None = None,
) -> str:
    updated_text = _insert_confirmed_skills(resume_text, accepted_skills or [])
    prompts = [item.strip() for item in accepted_suggestions if item.strip()]
    if not prompts:
        return updated_text
    additions = "\n\nNOTES TO REVIEW\n" + "\n".join(f"- {item}" for item in prompts)
    return updated_text.rstrip() + additions


def interview_tips(role: str) -> dict:
    from services.interview_service import generate_interview_questions

    payload = generate_interview_questions(role=role)
    return {
        "role": payload["role"],
        "questions": [
            {
                "question": item["question"],
                "example_answer": item["answer_framework"],
                "category": item["category"],
                "difficulty": item["difficulty"],
                "related_skill": item.get("related_skill", ""),
            }
            for item in payload["questions"]
        ],
        "tips": payload["tips"],
        "disclaimer": payload["disclaimer"],
    }


def analyze_all(
    resume_text: str,
    job_description: str,
    *,
    role: str = "",
    include_interview: bool = True,
    interview_limit: int = 12,
) -> dict:
    """Orchestrate the full analysis in one request.

    Imports are local to avoid a module-level cycle with ``ats_service``, which
    depends on the comparison functions in this module.
    """
    from services.ats_service import score_resume
    from services.interview_service import generate_interview_questions
    from services.job_service import analyze_job_description
    from services.learning_path_service import generate_learning_paths

    resume_text = normalize_text(resume_text)
    job_description = normalize_text(job_description)
    structured = extract_structured_resume(resume_text)
    resume_skills = structured["skills"]["all"]
    job = analyze_job_description(job_description)
    comparison = compare_resume_to_job(
        resume_text,
        resume_skills,
        job["required_skills"],
        job["preferred_skills"],
        resume_confidence=structured["confidence"],
    )
    ats = score_resume(
        resume_text,
        job_description,
        resume_skills=resume_skills,
        job=job,
        comparison=comparison,
        structured=structured,
    )

    gap_skills: list[str] = []
    requirements: dict[str, str] = {}
    evidence: dict[str, str] = {}
    for explanation in comparison["explanations"]:
        skill = explanation["skill"]
        status = explanation["status"]
        requirements[skill] = explanation["requirement"]
        evidence[skill] = status
        if status in {"missing", "partial"}:
            gap_skills.append(skill)

    # Required gaps come first, then preferred gaps, preserving report order.
    gap_skills.sort(
        key=lambda skill: (
            0 if requirements.get(skill) == "required" else 1,
            0 if evidence.get(skill) == "missing" else 1,
        )
    )
    suggestions = make_suggestions(comparison["missing_required"], resume_text)
    learning_paths = generate_learning_paths(
        gap_skills, evidence=evidence, requirements=requirements
    )
    interview = (
        generate_interview_questions(
            role or job["title"],
            required_skills=job["required_skills"],
            missing_skills=comparison["missing_required"],
            resume_skills=resume_skills,
            projects=structured["projects"],
            limit=interview_limit,
        )
        if include_interview
        else {"role": role or job["title"], "questions": [], "tips": [], "categories": [], "method": "disabled", "disclaimer": ""}
    )

    return {
        "structured_resume": structured,
        "resume_skills": resume_skills,
        "job": job,
        "comparison": comparison,
        "ats": ats,
        "suggestions": suggestions,
        "learning_paths": learning_paths,
        "interview": interview,
        "meta": {
            "resume_confidence": structured["confidence"],
            "resume_warnings": structured["warnings"],
            "job_confidence": job["confidence"],
            "job_warnings": job["warnings"],
            "resume_word_count": structured["word_count"],
            "job_word_count": job["word_count"],
            "semantic_matching": get_settings().enable_semantic_matching,
            "method": "hybrid-exact-synonym-implication-related-evidence",
            "disclaimer": comparison["disclaimer"],
        },
    }
