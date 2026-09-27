import json
import os
import re

from services.analyzer import SKILLS, extract_skills


_EXPERIENCE_HEADING = re.compile(r"^\s*(?:professional\s+)?experience\b|^\s*(?:work|employment)\s+history\b", re.I)
_OTHER_HEADING = re.compile(
    r"^\s*(?:education|skills?|technical skills|summary|profile|certifications?|projects?|volunteer|awards?)\b",
    re.I,
)
_BULLET = re.compile(r"^(\s*(?:[-*+]\s+|\d+[.)]\s+)?)(.*)$")
_METRIC = re.compile(r"(?:\b\d+(?:\.\d+)?\s?%|\$\s?\d|\b\d[\d,]*(?:\.\d+)?\s?(?:users|clients|customers|projects|hours|days|weeks|months|years|k|million)\b)", re.I)
_ACTION_START = re.compile(
    r"^(?:built|created|developed|designed|implemented|delivered|led|launched|"
    r"improved|increased|reduced|optimized|automated|analyzed|managed|"
    r"maintained|migrated|deployed|engineered|generated|established|streamlined|"
    r"resolved|integrated|collaborated|supported|configured|tested|wrote|"
    r"conducted|coordinated|owned|mentored|negotiated|achieved|introduced)\b",
    re.I,
)
_PREFIX_REWRITES = (
    (re.compile(r"^worked\s+on\s+", re.I), "Contributed to "),
    (re.compile(r"^worked\s+with\s+", re.I), "Collaborated with "),
    (re.compile(r"^helped\s+with\s+", re.I), "Supported "),
    (re.compile(r"^was\s+involved\s+in\s+", re.I), "Contributed to "),
    (re.compile(r"^did\s+", re.I), "Completed "),
)


def _try_openai_rewrite(resume_text: str, job_description: str) -> dict | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or os.getenv("ENABLE_OPENAI_REWRITER", "").lower() != "true":
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, timeout=25.0, max_retries=0)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Rewrite resume experience for relevance and clarity. Return a JSON object with "
                        "rewritten (string) and changes (array of strings). Preserve all factual claims; "
                        "never invent skills, responsibilities, employers, dates, or metrics. Do not add a "
                        "job keyword unless the resume supports it. Use [add a verified outcome metric] "
                        "when a metric would help but none was provided. Keep section structure and tone professional."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps({"resume_text": resume_text, "job_description": job_description}),
                },
            ],
        )
        content = response.choices[0].message.content
        if not content:
            return None
        result = json.loads(content)
        rewritten = result.get("rewritten")
        changes = result.get("changes")
        if not isinstance(rewritten, str) or not isinstance(changes, list) or not all(isinstance(item, str) for item in changes):
            return None
        return {"rewritten": rewritten, "changes": changes, "method": "openai"}
    except Exception:
        return None


def _rule_based_rewrite(resume_text: str, job_description: str) -> dict:
    job_skills = set(extract_skills(job_description))
    resume_skills = set(extract_skills(resume_text))
    supported_job_skills = [skill for skill in SKILLS if skill in job_skills and skill in resume_skills]
    lines = resume_text.splitlines()
    has_experience_heading = any(_EXPERIENCE_HEADING.match(line) for line in lines)
    in_experience = not has_experience_heading
    rewritten_lines = []
    improved_bullets = 0
    formatted_lines = 0
    metric_prompts = 0

    for line in lines:
        if _EXPERIENCE_HEADING.match(line):
            in_experience = True
            rewritten_lines.append(line)
            continue
        if _OTHER_HEADING.match(line):
            in_experience = False
            rewritten_lines.append(line)
            continue
        if not in_experience or not line.strip():
            rewritten_lines.append(line)
            continue

        match = _BULLET.match(line)
        prefix, content = match.groups() if match else ("", line)
        content = content.strip()
        is_weak_opening = bool(re.match(r"^(?:worked|helped|did|was involved)\b", content, re.I))
        is_action_sentence = len(content.split()) >= 4 and bool(_ACTION_START.match(content))
        if not content or not (prefix.strip() or is_weak_opening or is_action_sentence):
            rewritten_lines.append(line)
            continue

        if not prefix.strip():
            prefix = "- "
            formatted_lines += 1

        rewritten = content
        for pattern, replacement in _PREFIX_REWRITES:
            updated, count = pattern.subn(replacement, rewritten, count=1)
            if count:
                rewritten = updated
                improved_bullets += 1
                break
        if not _METRIC.search(rewritten):
            rewritten = rewritten.rstrip().rstrip(".!?;:") + " [add a verified outcome metric]."
            metric_prompts += 1
        rewritten_lines.append(prefix + rewritten)

    changes = []
    if improved_bullets:
        changes.append(f"Strengthened the opening wording on {improved_bullets} experience item(s).")
    if formatted_lines:
        changes.append(f"Formatted {formatted_lines} experience item(s) as resume bullets.")
    if supported_job_skills:
        changes.append("Highlighted existing job-aligned skills: " + ", ".join(supported_job_skills) + ".")
    missing_job_skills = [skill for skill in SKILLS if skill in job_skills and skill not in resume_skills]
    if missing_job_skills:
        changes.append(
            "Consider addressing these keywords only where your experience supports them: "
            + ", ".join(missing_job_skills[:8])
            + "."
        )
    if metric_prompts:
        changes.append(f"Added verified-outcome prompts to {metric_prompts} item(s); no metrics were invented.")
    if not changes:
        changes.append("No safely rewritable experience bullets were found; review the resume text manually.")

    return {"rewritten": "\n".join(rewritten_lines), "changes": changes, "method": "rule-based"}


def rewrite_resume(resume_text: str, job_description: str) -> dict:
    result = _try_openai_rewrite(resume_text, job_description)
    if result is None:
        result = _rule_based_rewrite(resume_text, job_description)
    return {
        "original": resume_text,
        "rewritten": result["rewritten"],
        "changes": result["changes"],
        "method": result["method"],
    }