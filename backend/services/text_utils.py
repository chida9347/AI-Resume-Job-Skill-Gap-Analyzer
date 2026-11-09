"""Shared text utilities: normalisation, sentence splitting and section detection."""

from __future__ import annotations

import re

SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "summary": (
        "summary",
        "professional summary",
        "profile",
        "professional profile",
        "objective",
        "career objective",
        "about",
        "about me",
    ),
    "experience": (
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "employment history",
        "work history",
        "career history",
        "relevant experience",
    ),
    "education": (
        "education",
        "academic background",
        "academic qualifications",
        "academic history",
        "qualifications",
    ),
    "skills": (
        "skills",
        "technical skills",
        "core skills",
        "core competencies",
        "competencies",
        "technologies",
        "tech stack",
        "technical proficiencies",
        "areas of expertise",
    ),
    "projects": (
        "projects",
        "personal projects",
        "academic projects",
        "selected projects",
        "key projects",
        "project experience",
    ),
    "certifications": (
        "certifications",
        "certificates",
        "certification",
        "licenses",
        "licenses & certifications",
        "certifications and licenses",
    ),
    "awards": ("awards", "honors", "honours", "achievements", "accomplishments"),
    "languages": ("languages", "language proficiency"),
    "volunteer": ("volunteer", "volunteer experience", "volunteering", "extracurricular", "extracurricular activities"),
    "publications": ("publications", "research", "research experience", "papers"),
}

_ALIAS_TO_SECTION = {
    alias: key for key, aliases in SECTION_ALIASES.items() for alias in aliases
}

_HEADING_INLINE = re.compile(r"^\s*([A-Za-z][A-Za-z &/+,.'-]{1,45}?)\s*:\s*(.*)$")
_HEADING_PLAIN = re.compile(r"^\s*([A-Za-z][A-Za-z &/+,.'-]{1,45})\s*$")
_HEADING_DECORATION = re.compile(r"^[\s\-_=*#|]+|[\s\-_=*#|]+$")

STOPWORDS = {
    "about", "above", "across", "after", "again", "against", "all", "also", "an", "and",
    "any", "are", "as", "at", "be", "because", "been", "before", "being", "between",
    "both", "but", "by", "can", "could", "did", "do", "does", "doing", "during", "each",
    "etc", "few", "for", "from", "further", "had", "has", "have", "having", "he", "her",
    "here", "hers", "herself", "him", "himself", "his", "how", "however", "i", "if", "in",
    "into", "is", "it", "its", "itself", "just", "may", "me", "might", "more", "most",
    "must", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once", "only",
    "or", "other", "our", "ours", "ourselves", "out", "over", "own", "per", "same", "she",
    "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them",
    "themselves", "then", "there", "these", "they", "this", "those", "through", "to",
    "too", "under", "until", "up", "very", "was", "we", "were", "what", "when", "where",
    "which", "while", "who", "whom", "why", "will", "with", "would", "you", "your",
    "yours", "yourself", "yourselves",
    # Job-posting boilerplate
    "ability", "applicant", "applicants", "candidate", "candidates", "company", "demonstrate",
    "desired", "develop", "environment", "equal", "employer", "experience", "including",
    "job", "join", "looking", "opportunity", "preferred", "provide", "qualification",
    "qualifications", "required", "requirement", "requirements", "responsibility",
    "responsibilities", "role", "seeking", "skill", "skills", "strong", "team", "teams",
    "using", "various", "work", "working", "years",
}

ACTION_VERBS = {
    "achieved", "adapted", "administered", "advised", "analyzed", "architected", "authored",
    "automated", "built", "collaborated", "communicated", "completed", "configured",
    "consolidated", "contributed", "converted", "coordinated", "created", "decreased",
    "defined", "delivered", "deployed", "designed", "developed", "diagnosed", "directed",
    "documented", "drove", "earned", "engineered", "enhanced", "established", "evaluated",
    "executed", "expanded", "facilitated", "generated", "guided", "identified", "implemented",
    "improved", "increased", "initiated", "integrated", "introduced", "launched", "led",
    "leveraged", "maintained", "managed", "migrated", "mentored", "modeled", "monitored",
    "negotiated", "optimized", "orchestrated", "organized", "owned", "partnered",
    "performed", "planned", "presented", "produced", "reduced", "refactored", "researched",
    "resolved", "reviewed", "scaled", "secured", "simplified", "streamlined", "supported",
    "tested", "trained", "transformed", "validated", "wrote",
}

WEAK_OPENERS = {
    "worked", "helped", "assisted", "responsible", "involved", "participated", "handled",
    "did", "was", "were", "tasked", "duties", "utilized", "used",
}

METRIC_PATTERN = re.compile(
    r"(?:\b\d+(?:\.\d+)?\s?%|\$\s?\d|\b\d[\d,]*(?:\.\d+)?\s?"
    r"(?:users|clients|customers|projects|hours|days|weeks|months|years|k|million|billion|requests|records|rows|transactions)\b)",
    re.IGNORECASE,
)

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_PATTERN = re.compile(
    r"(?:(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?){2,4}\d{2,4})"
)
LINKEDIN_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/[^\s,;)]+", re.IGNORECASE)
GITHUB_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[^\s,;)]+", re.IGNORECASE)
URL_PATTERN = re.compile(r"https?://[^\s,;)]+", re.IGNORECASE)
YEAR_PATTERN = re.compile(r"\b(?:19|20)\d{2}\b")
GPA_PATTERN = re.compile(
    r"\b(?:cgpa|gpa|grade|percentage|percent)\s*[:\-]?\s*(\d{1,3}(?:\.\d{1,2})?)\s*(?:/\s*(\d{1,3}(?:\.\d{1,2})?))?",
    re.IGNORECASE,
)


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", normalize_text(text))
    return [part.strip(" \t-*•·") for part in parts if part and part.strip(" \t-*•·")]


def _normalize_heading(value: str) -> str:
    value = _HEADING_DECORATION.sub("", value).strip().lower()
    value = re.sub(r"\s+", " ", value)
    value = value.strip(":.-—–")
    return value


def section_key_for_heading(line: str) -> tuple[str, str] | None:
    """Return (section_key, inline_content) when a line is a section heading."""
    stripped = line.strip()
    if not stripped or len(stripped) > 90:
        return None
    # Inline form first ("Experience: 5 years"), then the plain heading form
    # ("Experience"). The plain pattern is anchored so ordinary prose lines do
    # not match, and the candidate is validated against the alias table.
    match = _HEADING_INLINE.match(stripped)
    if match:
        candidate = _normalize_heading(match.group(1))
        key = _ALIAS_TO_SECTION.get(candidate)
        if key:
            return key, match.group(2).strip()
        return None

    match = _HEADING_PLAIN.match(stripped)
    if not match:
        return None
    candidate = _normalize_heading(match.group(1))
    key = _ALIAS_TO_SECTION.get(candidate)
    if not key:
        return None
    return key, ""


def detect_sections(text: str) -> dict:
    """Split a document into sections.

    Returns ``{"header": {...}, "sections": {key: {heading, lines, inline}}, "line_sections": [...]}``.
    Repeated headings (e.g. two "Experience" blocks) are merged.
    """
    lines = normalize_text(text).splitlines()
    header_lines: list[str] = []
    sections: dict[str, dict] = {}
    line_sections: list[str | None] = []
    current: str | None = None

    for line in lines:
        heading = section_key_for_heading(line)
        if heading:
            key, inline = heading
            section = sections.setdefault(key, {"heading": line.strip().rstrip(":"), "lines": [], "inline": []})
            if inline:
                section["inline"].append(inline)
            current = key
            line_sections.append(key)
            continue
        line_sections.append(current)
        if current is None:
            header_lines.append(line)
        else:
            sections[current]["lines"].append(line)

    return {
        "header": {"lines": header_lines},
        "sections": sections,
        "line_sections": line_sections,
    }


def section_text(sections: dict, key: str) -> str:
    section = sections.get("sections", {}).get(key)
    if not section:
        return ""
    return "\n".join([*section.get("inline", []), *section.get("lines", [])]).strip()


def section_for_line(sections: dict, line_index: int) -> str:
    mapping = sections.get("line_sections", [])
    if 0 <= line_index < len(mapping):
        return mapping[line_index] or "header"
    return "header"


def line_index_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, max(0, offset))


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9+#./-]*", text.lower())


def keywords(text: str, limit: int = 40) -> list[str]:
    from collections import Counter

    counts = Counter(
        token.strip("./-")
        for token in tokenize(text)
        if len(token.strip("./-")) >= 3 and token.strip("./-") not in STOPWORDS
    )
    return [word for word, _ in counts.most_common(limit)]


def first_nonempty_line(text: str) -> str:
    for line in normalize_text(text).splitlines():
        if line.strip():
            return line.strip()
    return ""
