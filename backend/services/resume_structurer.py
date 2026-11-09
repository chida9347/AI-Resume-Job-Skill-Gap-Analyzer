"""Structured resume extraction.

This module only reports information that is present in the text. When a field
cannot be found it is omitted and a warning is added. It never fills gaps with
invented values.
"""

from __future__ import annotations

import re

from services.skill_taxonomy import CATEGORIES, DISPLAY_NAMES, extract_canonical_skills
from services.text_utils import (
    ACTION_VERBS,
    EMAIL_PATTERN,
    GPA_PATTERN,
    GITHUB_PATTERN,
    LINKEDIN_PATTERN,
    METRIC_PATTERN,
    PHONE_PATTERN,
    URL_PATTERN,
    YEAR_PATTERN,
    detect_sections,
    first_nonempty_line,
    normalize_text,
    section_text,
)

_DEGREE = re.compile(
    r"\b(?:bachelor(?:'s)?|master(?:'s)?|ph\.?\s?d|doctorate|b\.?\s?tech|m\.?\s?tech|"
    r"b\.?\s?e\.?|m\.?\s?e\.?|b\.?\s?sc|m\.?\s?sc|b\.?\s?s\.?|m\.?\s?s\.?|mba|"
    r"b\.?\s?com|m\.?\s?com|associate(?:'s)?|diploma|high school|secondary school)\b",
    re.IGNORECASE,
)
_INSTITUTION = re.compile(
    r"\b(?:university|college|institute|school|academy|polytechnic|iit|nit|iiit|bits)\b",
    re.IGNORECASE,
)
_DURATION = re.compile(
    r"(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+)?"
    r"(?:19|20)\d{2}\s*(?:[-–—]|to)\s*(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+)?"
    r"(?:(?:19|20)\d{2}|present|current)",
    re.IGNORECASE,
)
_BULLET = re.compile(r"^\s*(?:[-*+•·▪◦]|\d+[.)])\s*")
_JOB_TITLE = re.compile(
    r"\b(?:engineer|developer|analyst|scientist|manager|designer|consultant|intern|"
    r"architect|administrator|specialist|associate|director|lead|head|officer|assistant|"
    r"coordinator|researcher|tester|programmer|technician)\b",
    re.IGNORECASE,
)
_CERT_ISSUER = re.compile(r"\b(?:by|from|issued by|provided by|via)\b", re.IGNORECASE)
_NOT_NAME = re.compile(r"\b(?:resume|curriculum vitae|cv|profile|contact)\b", re.IGNORECASE)


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" |,;-–—")


def _find_phone(text: str) -> str:
    for match in PHONE_PATTERN.finditer(text):
        digits = re.sub(r"\D", "", match.group(0))
        if 7 <= len(digits) <= 15:
            return _clean(match.group(0))
    return ""


def _extract_contact(text: str, sections: dict) -> dict:
    header = "\n".join(sections["header"]["lines"])
    search_area = header or text
    email_match = EMAIL_PATTERN.search(text)
    linkedin_match = LINKEDIN_PATTERN.search(text)
    github_match = GITHUB_PATTERN.search(text)
    urls = URL_PATTERN.findall(text)
    portfolio = ""
    for url in urls:
        lowered = url.lower()
        if "linkedin.com" in lowered or "github.com" in lowered:
            continue
        portfolio = url.rstrip(".,;)")
        break

    name = ""
    for line in search_area.splitlines():
        candidate = _clean(line.split("|")[0])
        if (
            candidate
            and len(candidate) <= 60
            and not EMAIL_PATTERN.search(candidate)
            and not URL_PATTERN.search(candidate)
            and not _NOT_NAME.search(candidate)
            and not re.search(r"\d", candidate)
            and len(candidate.split()) <= 5
        ):
            name = candidate
            break

    return {
        "name": name,
        "email": email_match.group(0) if email_match else "",
        "phone": _find_phone(search_area),
        "linkedin": linkedin_match.group(0).rstrip(".,;)") if linkedin_match else "",
        "github": github_match.group(0).rstrip(".,;)") if github_match else "",
        "portfolio": portfolio,
    }


def _blocks(text: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.strip():
            current.append(line.rstrip())
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def _parse_education(text: str) -> list[dict]:
    entries: list[dict] = []
    for block in _blocks(text):
        degree_lines = [line for line in block if _DEGREE.search(line)]
        institution_lines = [line for line in block if _INSTITUTION.search(line)]
        if not degree_lines and not institution_lines:
            continue
        joined = " ".join(block)
        year_matches = YEAR_PATTERN.findall(joined)
        gpa_match = GPA_PATTERN.search(joined)
        details = [_clean(_BULLET.sub("", line)) for line in block if _BULLET.match(line)]
        entries.append(
            {
                "institution": _clean(institution_lines[0]) if institution_lines else "",
                "degree": _clean(degree_lines[0]) if degree_lines else "",
                "specialization": _specialization(joined),
                "graduation_year": year_matches[-1] if year_matches else "",
                "gpa": gpa_match.group(1) if gpa_match else "",
                "details": details,
            }
        )
    return entries


def _specialization(text: str) -> str:
    match = re.search(
        r"\b(?:in|of)\s+([A-Z][A-Za-z&/ ]{2,60}?)(?:\s*(?:,|\(|\)|\||$|from|at)\b)",
        text,
    )
    if not match:
        return ""
    value = _clean(match.group(1))
    return value if len(value.split()) <= 6 else ""


def _parse_experience(text: str) -> list[dict]:
    entries: list[dict] = []
    for block in _blocks(text):
        first = _clean(_BULLET.sub("", block[0]))
        rest = block[1:]
        duration_match = _DURATION.search(" ".join(block))
        if not (duration_match or _JOB_TITLE.search(first) or len(block) >= 2):
            continue
        # Split "Title | Company | Dates" / "Company — Title" heuristically.
        parts = [part for part in re.split(r"\s+[|·•]\s+|\s+[–—]\s+|\s+at\s+", first) if part.strip()]
        title, company = "", ""
        for part in parts:
            if _JOB_TITLE.search(part) and not title:
                title = _clean(part)
            elif not company and not _DURATION.search(part):
                company = _clean(part)
        if not title and _JOB_TITLE.search(first):
            title = first
        responsibilities = []
        achievements = []
        for line in rest:
            content = _clean(_BULLET.sub("", line))
            if not content:
                continue
            if METRIC_PATTERN.search(content):
                achievements.append(content)
            elif _BULLET.match(line) or any(content.lower().startswith(verb) for verb in ACTION_VERBS):
                responsibilities.append(content)
        entries.append(
            {
                "company": company,
                "title": title,
                "duration": duration_match.group(0) if duration_match else "",
                "responsibilities": responsibilities,
                "achievements": achievements,
            }
        )
    return entries


def _parse_projects(text: str) -> list[dict]:
    entries: list[dict] = []
    for block in _blocks(text):
        if not block:
            continue
        title = _clean(_BULLET.sub("", block[0]))
        title = re.sub(r"^(?:project|title)\s*[:\-]\s*", "", title, flags=re.IGNORECASE)
        if not title:
            continue
        body = " ".join(block[1:]) if len(block) > 1 else ""
        technologies = extract_canonical_skills(body or title)
        contributions = []
        outcomes = []
        for line in block[1:]:
            content = _clean(_BULLET.sub("", line))
            if not content:
                continue
            if METRIC_PATTERN.search(content):
                outcomes.append(content)
            else:
                contributions.append(content)
        entries.append(
            {
                "title": title,
                "description": _clean(body)[:800],
                "technologies": technologies,
                "contributions": contributions,
                "outcomes": outcomes,
            }
        )
    return entries


def _parse_certifications(text: str) -> list[dict]:
    entries = []
    for block in _blocks(text):
        for line in block:
            content = _clean(_BULLET.sub("", line))
            if not content:
                continue
            issuer = ""
            issuer_match = _CERT_ISSUER.search(content)
            if issuer_match:
                issuer = _clean(content[issuer_match.end():])
                content = _clean(content[: issuer_match.start()])
            elif "|" in content:
                content, issuer = (_clean(part) for part in content.split("|", 1))
            year = YEAR_PATTERN.search(line)
            entries.append(
                {
                    "name": content,
                    "issuer": issuer,
                    "date": year.group(0) if year else "",
                }
            )
    return entries


def _parse_simple_lines(text: str) -> list[str]:
    values = []
    for line in text.splitlines():
        content = _clean(_BULLET.sub("", line))
        if content:
            values.append(content)
    return values


def extract_structured_resume(text: str) -> dict:
    text = normalize_text(text)
    sections = detect_sections(text)
    contact = _extract_contact(text, sections)
    summary = section_text(sections, "summary")
    skills_text = section_text(sections, "skills")
    education_text = section_text(sections, "education")
    experience_text = section_text(sections, "experience")
    projects_text = section_text(sections, "projects")
    certifications_text = section_text(sections, "certifications")

    skills = extract_canonical_skills(text)
    by_category: dict[str, list[str]] = {}
    for skill in skills:
        from services.skill_taxonomy import category_of

        by_category.setdefault(category_of(skill), []).append(DISPLAY_NAMES.get(skill, skill))

    education = _parse_education(education_text) if education_text else []
    experience = _parse_experience(experience_text) if experience_text else []
    projects = _parse_projects(projects_text) if projects_text else []
    certifications = _parse_certifications(certifications_text) if certifications_text else []
    awards = _parse_simple_lines(section_text(sections, "awards"))
    languages = _parse_simple_lines(section_text(sections, "languages"))

    word_count = len(text.split())
    warnings: list[str] = []
    confidence = 0
    if contact.get("email"):
        confidence += 20
    else:
        warnings.append("No email address was detected.")
    if contact.get("phone"):
        confidence += 8
    if contact.get("name"):
        confidence += 7
    if skills:
        confidence += 18
    else:
        warnings.append("No recognised skills were detected. The resume may use uncommon terminology.")
    if experience:
        confidence += 18
    else:
        warnings.append("No clearly structured work experience section was detected.")
    if education:
        confidence += 12
    else:
        warnings.append("No clearly structured education section was detected.")
    if projects:
        confidence += 10
    else:
        warnings.append("No clearly structured projects section was detected.")
    if summary:
        confidence += 4
    if certifications:
        confidence += 3
    if word_count < 80:
        confidence = min(confidence, 35)
        warnings.append("The document is very short; extraction confidence is low.")

    section_presence = {
        key: bool(section_text(sections, key).strip()) for key in
        ("summary", "skills", "experience", "education", "projects", "certifications")
    }
    missing_information = [
        label
        for key, label in (
            ("summary", "professional summary"),
            ("skills", "skills section"),
            ("experience", "work experience"),
            ("education", "education"),
            ("projects", "projects"),
            ("certifications", "certifications"),
        )
        if not section_presence[key]
    ]

    return {
        "contact": contact,
        "summary": summary,
        "skills": {
            "all": skills,
            "by_category": by_category,
            "category_count": len(by_category),
            "total": len(skills),
            "from_skills_section": extract_canonical_skills(skills_text) if skills_text else [],
        },
        "education": education,
        "experience": experience,
        "projects": projects,
        "certifications": certifications,
        "awards": awards,
        "languages": languages,
        "section_presence": section_presence,
        "missing_information": missing_information,
        "word_count": word_count,
        "confidence": min(100, confidence),
        "warnings": warnings,
    }


def skill_evidence(text: str, skill: str) -> list[dict]:
    """Locate a canonical skill and classify how strongly it is demonstrated."""
    from services.skill_taxonomy import SKILL_BY_NAME

    entry = SKILL_BY_NAME.get(skill)
    if not entry:
        return []
    sections = detect_sections(text)
    lines = text.splitlines()
    evidence: list[dict] = []
    lowered = text.lower()
    aliases = sorted(entry.aliases, key=len, reverse=True)
    for alias in aliases:
        pattern = re.compile(r"(?<![A-Za-z0-9])" + re.escape(alias) + r"(?![A-Za-z0-9])", re.IGNORECASE)
        for match in pattern.finditer(text):
            line_index = text.count("\n", 0, match.start())
            line = lines[line_index].strip() if line_index < len(lines) else ""
            section = sections["line_sections"][line_index] if line_index < len(sections["line_sections"]) else "header"
            section = section or "header"
            content = _clean(_BULLET.sub("", line))
            words = content.split()
            has_action = any(word.strip(".,;:").lower() in ACTION_VERBS for word in words)
            has_metric = bool(METRIC_PATTERN.search(content))
            if section in {"experience", "projects"} and (has_action or has_metric) and len(words) >= 5:
                strength = "strong"
            elif section in {"skills", "summary", "education"} or len(words) < 5:
                strength = "mentioned"
            else:
                strength = "mentioned"
            evidence.append(
                {
                    "skill": skill,
                    "section": section,
                    "sentence": content[:320],
                    "strength": strength,
                    "has_metric": has_metric,
                }
            )
            if len(evidence) >= 3:
                return evidence
    # Fall back to a section-level mention for aliases with unusual punctuation.
    if lowered.count(entry.display.lower()):
        return evidence
    return evidence
