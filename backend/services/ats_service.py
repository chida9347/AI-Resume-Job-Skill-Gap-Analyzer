import re
from collections import Counter

from services.analyzer import SKILLS, extract_skills


_STOPWORDS = {
    "about", "across", "after", "all", "also", "an", "and", "any", "are",
    "as", "at", "based", "be", "been", "between", "both", "build", "by",
    "can", "candidate", "company", "desired", "develop", "do", "each",
    "etc", "experience", "for", "from", "have", "having", "help", "high",
    "in", "include", "including", "is", "it", "join", "job", "looking",
    "make", "more", "must", "new", "of", "on", "or", "our", "over",
    "preferred", "provide", "qualifications", "responsibilities", "role",
    "seeking", "should", "skill", "skills", "strong", "such", "team",
    "that", "the", "their", "this", "to", "use", "using", "various",
    "we", "what", "which", "will", "with", "work", "working", "you",
    "your",
}
_SECTION_HEADINGS = (
    r"skills?|technical skills|core competencies|competencies|"
    r"experience|work history|employment history|professional experience|"
    r"education|academic background|certifications?|projects?"
)
_METRIC_PATTERN = re.compile(
    r"(?:\b\d+(?:\.\d+)?\s?%|\$\s?\d|\b\d[\d,]*(?:\.\d+)?\s?(?:users|clients|customers|projects|hours|days|weeks|months|years|k|million)\b)",
    re.IGNORECASE,
)


def _keyword_present(keyword: str, text: str) -> bool:
    aliases = SKILLS.get(keyword, [keyword])
    return any(
        re.search(r"(?<![a-z0-9])" + re.escape(alias.strip()) + r"(?![a-z0-9])", text, re.IGNORECASE)
        for alias in aliases
    )


def _extract_keywords(text: str) -> list[str]:
    skill_keywords = extract_skills(text)
    tokens = re.findall(r"[a-z][a-z0-9+#./-]*", text.lower())
    counts = Counter(token.strip("./-") for token in tokens)
    generic_keywords = [
        token
        for token, _ in sorted(counts.items(), key=lambda item: -item[1])
        if len(token) >= 4 and token not in _STOPWORDS and not token.isdigit()
    ]
    return list(dict.fromkeys([*skill_keywords, *generic_keywords]))[:40]


def _section_content(resume_text: str, heading_pattern: str) -> bool:
    lines = resume_text.splitlines()
    heading = re.compile(r"^\s*(?:" + heading_pattern + r")\s*:?(?:\s+(.*))?$", re.IGNORECASE)
    any_heading = re.compile(r"^\s*(?:" + _SECTION_HEADINGS + r")\s*:?(?:\s+.*)?$", re.IGNORECASE)
    for index, line in enumerate(lines):
        match = heading.match(line)
        if not match:
            continue
        if match.group(1) and match.group(1).strip():
            return True
        for following in lines[index + 1:]:
            if any_heading.match(following):
                break
            if following.strip():
                return True
        return False
    return False


def _section_scores(resume_text: str) -> dict[str, int]:
    skills_content = _section_content(resume_text, r"skills?|technical skills|core competencies|competencies")
    experience_content = _section_content(resume_text, r"experience|work history|employment history|professional experience")
    education_content = _section_content(resume_text, r"education|academic background")
    has_skill_mentions = bool(extract_skills(resume_text))
    has_education_mentions = bool(re.search(r"\b(?:bachelor|master|ph\.?d|degree|university|college|diploma)\b", resume_text, re.I))

    return {
        "skills": 100 if skills_content else 60 if has_skill_mentions else 0,
        "experience": 100 if experience_content else 0,
        "education": 100 if education_content else 60 if has_education_mentions else 0,
    }


def _formatting_quality(resume_text: str) -> int:
    score = 100
    words = resume_text.split()
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    if len(words) < 75:
        score -= 20
    if len(words) > 12_000:
        score -= 15
    if len(lines) < 4:
        score -= 15
    if sum(len(line) > 240 for line in lines) > 2:
        score -= 15
    if lines and max(Counter(line.lower() for line in lines).values()) > 2:
        score -= 10
    return max(0, min(100, score))


def score_resume(resume_text: str, job_description: str) -> dict:
    job_keywords = _extract_keywords(job_description)
    matched_keywords = [keyword for keyword in job_keywords if _keyword_present(keyword, resume_text)]
    missing_keywords = [keyword for keyword in job_keywords if keyword not in matched_keywords]
    keyword_match = round(len(matched_keywords) / len(job_keywords) * 100) if job_keywords else 0

    sections = _section_scores(resume_text)
    section_average = (
        sections["skills"] * 0.30
        + sections["experience"] * 0.45
        + sections["education"] * 0.25
    )
    formatting = _formatting_quality(resume_text)
    ats_score = round(keyword_match * 0.60 + section_average * 0.25 + formatting * 0.15)

    feedback = [f"Missing important keyword: {keyword}" for keyword in missing_keywords[:5]]
    if sections["skills"] < 70:
        feedback.append("Add a clearly labeled skills section with relevant tools and competencies.")
    if sections["experience"] < 70:
        feedback.append("Add a clearly labeled experience section with role, employer, and achievement details.")
    elif not _METRIC_PATTERN.search(resume_text):
        feedback.append("Experience section lacks measurable achievements; add verified outcomes where possible.")
    if sections["education"] < 70:
        feedback.append("Add a clearly labeled education section with relevant qualifications.")
    if formatting < 80:
        feedback.append("Improve text structure with concise bullets, consistent headings, and readable line lengths.")
    if not job_keywords:
        feedback.append("No relevant keywords could be identified from the job description.")

    return {
        "ats_score": ats_score,
        "keyword_match": keyword_match,
        "job_keywords": job_keywords,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "section_score": sections,
        "formatting_quality": formatting,
        "feedback": feedback,
    }