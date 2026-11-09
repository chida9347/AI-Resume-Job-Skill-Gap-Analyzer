"""Job description intelligence.

The classifier is deliberately conservative: a skill is only "required" when the
surrounding language or section says so. Skills mentioned in responsibilities or
company prose are reported as "mentioned" and do not inflate required coverage.
"""

from __future__ import annotations

import re

from services.skill_taxonomy import DISPLAY_NAMES, category_of, extract_canonical_skills, find_occurrences
from services.text_utils import (
    EMAIL_PATTERN,
    YEAR_PATTERN,
    keywords,
    normalize_text,
)

_REQUIRED_CUES = re.compile(
    r"\b(?:required|requirement|requirements|must(?:\s+have)?|minimum|min\.?|at\s+least|"
    r"proficien(?:t|cy)|expertise|hands[- ]on|strong\s+(?:experience|knowledge|background)|"
    r"solid\s+(?:experience|understanding)|you\s+(?:have|bring)|essential|mandatory|need(?:ed)?)\b",
    re.IGNORECASE,
)
_PREFERRED_CUES = re.compile(
    r"\b(?:preferred|nice\s+to\s+have|good\s+to\s+have|bonus|a\s+plus|plus|desirable|"
    r"desired|advantage(?:ous)?|ideally|familiarity\s+with|exposure\s+to)\b",
    re.IGNORECASE,
)
_EXPERIENCE_PATTERN = re.compile(
    r"\b(\d{1,2})\s*(?:\+|plus)?\s*(?:[-–—]|to)?\s*(\d{1,2})?\s*(?:\+)?\s*years?"
    r"(?:\s+of)?(?:\s+(?:professional|relevant|industry|hands-on))?\s+experience\b",
    re.IGNORECASE,
)
_EDUCATION_PATTERN = re.compile(
    r"\b(?:bachelor(?:'s)?|master(?:'s)?|ph\.?\s?d|doctorate|b\.?\s?tech|m\.?\s?tech|"
    r"b\.?\s?e\.?|m\.?\s?e\.?|b\.?\s?sc|m\.?\s?sc|mba|degree|diploma)\b",
    re.IGNORECASE,
)
_BULLET = re.compile(r"^\s*(?:[-*+•·▪◦]|\d+[.)])\s*")

_JOB_SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "responsibilities": (
        "responsibilities", "what you'll do", "what you will do", "the role", "your role",
        "duties", "key responsibilities", "day to day", "day-to-day",
    ),
    "requirements": (
        "requirements", "qualifications", "minimum qualifications", "basic qualifications",
        "required qualifications", "what we're looking for", "what we are looking for",
        "who you are", "must have", "must-have", "skills", "experience",
    ),
    "preferred": (
        "preferred qualifications", "preferred skills", "nice to have", "nice-to-have",
        "bonus points", "bonus", "desired", "good to have", "additional qualifications",
        "plus",
    ),
    "about": ("about us", "about the company", "company", "who we are", "overview", "the company"),
    "benefits": ("benefits", "perks", "what we offer", "compensation", "why join us"),
    "eligibility": ("eligibility", "other requirements", "additional requirements", "work authorization"),
}

_SECTION_LOOKUP = {alias: key for key, aliases in _JOB_SECTION_ALIASES.items() for alias in aliases}

# Cue markers can appear mid-line ("Required: Python. Preferred: Docker.").
# Splitting on them keeps one line from being classified entirely by whichever
# cue happens to be checked first.
_CUE_MARKER = re.compile(
    r"\b(?P<cue>required|requirements?|must(?:\s+have)?|minimum|at\s+least|"
    r"proficien(?:t|cy)|expertise|hands[- ]on|essential|mandatory|"
    r"preferred|nice\s+to\s+have|good\s+to\s+have|bonus|a\s+plus|plus|"
    r"desirable|desired|advantage(?:ous)?|ideally)\b",
    re.IGNORECASE,
)
_REQUIRED_MARKERS = {
    "required", "requirement", "requirements", "must", "must have", "minimum",
    "at least", "proficient", "proficiency", "expertise", "hands-on",
    "hands on", "essential", "mandatory",
}


def _marker_level(cue: str) -> str:
    return "required" if cue.casefold() in _REQUIRED_MARKERS else "preferred"


def _line_segments(line: str, section: str) -> list[tuple[str, str]]:
    """Split a line at requirement/preference cues.

    A cue followed by ``:`` or ``-`` governs the text that follows it
    ("Required: Python"). A trailing cue governs the text before it
    ("Python is required"). Everything else inherits the section default.
    """
    markers = list(_CUE_MARKER.finditer(line))
    if not markers:
        return [(line, _classify_line(line, section))]

    cuts: list[tuple[int, re.Match[str], bool]] = []
    for marker in markers:
        following = line[marker.end():].lstrip()
        leading = following.startswith((":", "-", "–", "—"))
        cuts.append((marker.start() if leading else marker.end(), marker, leading))

    points = [0, *[cut[0] for cut in cuts], len(line)]
    segments: list[tuple[str, str]] = []
    for index in range(len(points) - 1):
        start, end = points[index], points[index + 1]
        text = line[start:end].strip(" ,;:-–—")
        if not text:
            continue
        level = ""
        for position, marker, leading in cuts:
            if leading and position == start:
                level = _marker_level(marker.group("cue"))
                break
        if not level:
            for position, marker, leading in cuts:
                if not leading and position == end:
                    level = _marker_level(marker.group("cue"))
                    break
        segments.append((text, level or _classify_line(text, section)))
    return segments or [(line, _classify_line(line, section))]



def _job_section(line: str) -> str | None:
    stripped = line.strip().lower().rstrip(":")
    if not stripped or len(stripped) > 70:
        return None
    return _SECTION_LOOKUP.get(stripped)


def _classify_line(line: str, section: str) -> str:
    if _PREFERRED_CUES.search(line):
        return "preferred"
    if _REQUIRED_CUES.search(line):
        return "required"
    if section == "preferred":
        return "preferred"
    if section in {"requirements", "eligibility"}:
        return "required"
    return "mentioned"


def _extract_title(text: str) -> str:
    explicit = re.search(
        r"^\s*(?:job\s+title|position|role|title)\s*[:\-]\s*(.+)$",
        text,
        re.IGNORECASE | re.MULTILINE,
    )
    if explicit:
        return explicit.group(1).strip()[:160]
    looking_for = re.search(
        r"(?:looking for|seeking|hiring)\s+(?:an?\s+)?([A-Z][A-Za-z0-9 /+.-]{2,70})",
        text,
    )
    if looking_for:
        return looking_for.group(1).strip(" .,")[:160]
    first = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if first and len(first) <= 90 and not re.search(r"[.!?]$", first):
        return first[:160]
    return ""


def _extract_company(text: str) -> str:
    explicit = re.search(r"^\s*company\s*[:\-]\s*(.+)$", text, re.IGNORECASE | re.MULTILINE)
    if explicit:
        return explicit.group(1).strip()[:160]
    about = re.search(r"^about\s+([A-Z][A-Za-z0-9&.,' -]{2,60})\s*$", text, re.IGNORECASE | re.MULTILINE)
    if about:
        return about.group(1).strip()[:160]
    at_company = re.search(r"\bat\s+([A-Z][A-Za-z0-9&.'-]+(?:\s+[A-Z][A-Za-z0-9&.'-]+){0,3})\b", text)
    if at_company:
        return at_company.group(1).strip()[:160]
    return ""


def _extract_experience(text: str) -> dict:
    match = _EXPERIENCE_PATTERN.search(text)
    if not match:
        return {"min_years": None, "max_years": None, "raw": ""}
    low = int(match.group(1))
    high = int(match.group(2)) if match.group(2) else None
    return {"min_years": low, "max_years": high, "raw": match.group(0)}


def _extract_education(text: str) -> dict:
    lines = []
    required = False
    for line in text.splitlines():
        if _EDUCATION_PATTERN.search(line) and len(line.strip()) <= 240:
            cleaned = _BULLET.sub("", line).strip()
            if cleaned and cleaned not in lines:
                lines.append(cleaned)
                if not _PREFERRED_CUES.search(line):
                    required = True
    return {"mentions": lines[:6], "required": required}


def _extract_responsibilities(text: str) -> list[str]:
    lines: list[str] = []
    current = None
    for line in text.splitlines():
        heading = _job_section(line)
        if heading:
            current = heading
            continue
        if current == "responsibilities":
            cleaned = _BULLET.sub("", line).strip()
            if cleaned and len(cleaned) > 12:
                lines.append(cleaned[:400])
    if not lines:
        # Fall back to bullet lines that start with an action verb.
        from services.text_utils import ACTION_VERBS

        for line in text.splitlines():
            if _BULLET.match(line):
                cleaned = _BULLET.sub("", line).strip()
                if cleaned.split(" ")[0].lower() in ACTION_VERBS and len(cleaned) > 15:
                    lines.append(cleaned[:400])
    return list(dict.fromkeys(lines))[:15]


def _extract_eligibility(text: str) -> list[str]:
    current = None
    values = []
    for line in text.splitlines():
        heading = _job_section(line)
        if heading:
            current = heading
            continue
        if current == "eligibility":
            cleaned = _BULLET.sub("", line).strip()
            if cleaned:
                values.append(cleaned[:300])
    return list(dict.fromkeys(values))[:8]


def analyze_job_description(text: str) -> dict:
    text = normalize_text(text)
    warnings: list[str] = []
    if len(text.split()) < 25:
        warnings.append("The job description is short; required/preferred classification may be incomplete.")

    skill_levels: dict[str, str] = {}
    skill_context: dict[str, str] = {}
    current_section = "about"

    for line in text.splitlines():
        heading = _job_section(line)
        if heading:
            current_section = heading
            continue
        if not line.strip():
            continue
        for segment_text, level in _line_segments(line, current_section):
            for occurrence in find_occurrences(segment_text):
                skill = occurrence["skill"]
                existing = skill_levels.get(skill)
                priority = {"required": 3, "preferred": 2, "mentioned": 1}
                if existing is None or priority[level] > priority[existing]:
                    skill_levels[skill] = level
                    skill_context[skill] = line.strip()[:300]

    # A skill in the title is relevant but not automatically mandatory.
    title = _extract_title(text)
    for skill in extract_canonical_skills(title):
        skill_levels.setdefault(skill, "mentioned")

    required = [skill for skill in skill_levels if skill_levels[skill] == "required"]
    preferred = [skill for skill in skill_levels if skill_levels[skill] == "preferred"]
    mentioned = [skill for skill in skill_levels if skill_levels[skill] == "mentioned"]

    # Preserve reading order rather than taxonomy order for a natural UI.
    order = {}
    for occurrence in find_occurrences(text):
        order.setdefault(occurrence["skill"], occurrence["start"])
    for group in (required, preferred, mentioned):
        group.sort(key=lambda skill: order.get(skill, 10**9))

    if not required and preferred:
        warnings.append("No mandatory skills were detected; preferred skills are shown separately.")
    if not required and not preferred:
        warnings.append("No recognised technical skills were detected in this description.")

    experience = _extract_experience(text)
    education = _extract_education(text)
    responsibilities = _extract_responsibilities(text)
    eligibility = _extract_eligibility(text)
    important = list(
        dict.fromkeys(
            [
                *required,
                *preferred,
                *[
                    word
                    for word in keywords(text, limit=30)
                    if word not in {skill for skill in skill_levels}
                ],
            ]
        )
    )[:40]

    confidence = 0
    if title:
        confidence += 20
    if required:
        confidence += 30
    if preferred:
        confidence += 10
    if responsibilities:
        confidence += 15
    if experience["min_years"] is not None:
        confidence += 10
    if education["mentions"]:
        confidence += 5
    if len(text.split()) >= 80:
        confidence += 10
    if len(text.split()) < 40:
        confidence = min(confidence, 40)

    email_match = EMAIL_PATTERN.search(text)

    return {
        "title": title,
        "company": _extract_company(text),
        "required_skills": required,
        "preferred_skills": preferred,
        "mentioned_skills": mentioned,
        "skills": [*required, *preferred, *mentioned],
        # Legacy alias: every recognised skill in reading order.
        "technical_skills": [*required, *preferred, *mentioned],
        "skill_levels": skill_levels,
        "skill_context": skill_context,
        "skill_labels": {skill: DISPLAY_NAMES.get(skill, skill.title()) for skill in skill_levels},
        "skill_categories": {skill: category_of(skill) for skill in skill_levels},
        "experience": experience,
        "education": education,
        "responsibilities": responsibilities,
        "eligibility": eligibility,
        "important_keywords": important,
        "word_count": len(text.split()),
        "confidence": min(100, confidence),
        "warnings": warnings,
        "contact_email": email_match.group(0) if email_match else "",
        "years_mentioned": sorted(set(YEAR_PATTERN.findall(text))),
    }
