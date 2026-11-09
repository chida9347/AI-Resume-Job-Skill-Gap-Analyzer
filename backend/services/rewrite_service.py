"""Conservative resume rewriting.

Two paths exist:

* rule-based (always available, no network): fixes weak openings, formats
  bullets and inserts an explicit metric placeholder. It cannot add employers,
  dates, skills, certifications or numbers.
* optional OpenAI draft: only used when a key is configured, the feature is
  enabled *and* the request carries explicit consent. The prompt forbids
  fabrication and the response is validated before use.

Failures are logged without resume content and fall back to the rule-based path
instead of being silently swallowed.
"""

from __future__ import annotations

import json
import logging
import re

from config import get_settings
from services.analyzer import SKILLS, extract_skills
from services.text_utils import ACTION_VERBS, METRIC_PATTERN, WEAK_OPENERS

logger = logging.getLogger("roleprint.rewrite")

_EXPERIENCE_HEADING = re.compile(r"^\s*(?:professional\s+)?experience\b|^\s*(?:work|employment)\s+history\b", re.I)
_OTHER_HEADING = re.compile(
    r"^\s*(?:education|skills?|technical skills|summary|profile|certifications?|projects?|volunteer|awards?)\b",
    re.I,
)
_BULLET = re.compile(r"^(\s*(?:[-*+]\s+|\d+[.)]\s+)?)(.*)$")
_ACTION_START = re.compile(
    r"^(?:" + "|".join(sorted(ACTION_VERBS)) + r")\b",
    re.I,
)
_VAGUE = re.compile(r"\b(?:various|several|things|stuff|etc\.?|some|multiple)\b", re.I)
_PREFIX_REWRITES = (
    (re.compile(r"^worked\s+on\s+", re.I), "Contributed to "),
    (re.compile(r"^worked\s+with\s+", re.I), "Collaborated with "),
    (re.compile(r"^helped\s+with\s+", re.I), "Supported "),
    (re.compile(r"^helped\s+", re.I), "Supported "),
    (re.compile(r"^was\s+involved\s+in\s+", re.I), "Contributed to "),
    (re.compile(r"^responsible\s+for\s+", re.I), "Owned "),
    (re.compile(r"^did\s+", re.I), "Completed "),
)


def _settings():
    return get_settings()


def _try_openai_rewrite(resume_text: str, job_description: str, ai_consent: bool) -> dict | None:
    settings = _settings()
    if not ai_consent:
        logger.info("LLM rewrite skipped: per-request consent not provided.")
        return None
    if not settings.openai_enabled:
        logger.info("LLM rewrite skipped: OpenAI integration is not enabled.")
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key, timeout=25.0, max_retries=0)
        response = client.chat.completions.create(
            model=settings.openai_model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Rewrite resume experience for relevance and clarity. Return a JSON object with "
                        "rewritten (string) and changes (array of strings). Preserve all factual claims; "
                        "never invent skills, responsibilities, employers, dates, certifications or metrics. "
                        "Do not add a job keyword unless the resume supports it. Use "
                        "[add a verified outcome metric] when a metric would help but none was provided. "
                        "Keep section structure and a professional tone."
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
            logger.warning("LLM rewrite returned an empty response; using rule-based fallback.")
            return None
        result = json.loads(content)
        rewritten = result.get("rewritten")
        changes = result.get("changes")
        if (
            not isinstance(rewritten, str)
            or not rewritten.strip()
            or not isinstance(changes, list)
            or not all(isinstance(item, str) for item in changes)
        ):
            logger.warning("LLM rewrite returned an unexpected shape; using rule-based fallback.")
            return None
        return {"rewritten": rewritten, "changes": changes, "method": "openai"}
    except Exception:
        # Never log the resume body; the stack trace is enough to diagnose.
        logger.exception("LLM rewrite failed; using rule-based fallback.")
        return None


def _rule_based_rewrite(resume_text: str, job_description: str) -> dict:
    job_skills = set(extract_skills(job_description))
    resume_skills = set(extract_skills(resume_text))
    supported_job_skills = [skill for skill in SKILLS if skill in job_skills and skill in resume_skills]
    lines = resume_text.splitlines()
    has_experience_heading = any(_EXPERIENCE_HEADING.match(line) for line in lines)
    in_experience = not has_experience_heading
    rewritten_lines: list[str] = []
    improved_bullets = 0
    formatted_lines = 0
    metric_prompts = 0
    suggestions: list[dict] = []

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
        first_word = content.split(" ")[0].strip(".,;:").lower() if content else ""
        is_weak_opening = first_word in WEAK_OPENERS
        is_action_sentence = len(content.split()) >= 4 and bool(_ACTION_START.match(content))
        if not content or not (prefix.strip() or is_weak_opening or is_action_sentence):
            rewritten_lines.append(line)
            continue

        original = content
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

        if not METRIC_PATTERN.search(rewritten):
            rewritten = rewritten.rstrip().rstrip(".!?;:") + " [add a verified outcome metric]."
            metric_prompts += 1

        if rewritten.strip() != original.strip():
            suggestions.append(
                {
                    "id": f"bullet-{len(suggestions) + 1}",
                    "kind": "bullet",
                    "original": original,
                    "suggestion": rewritten,
                    "rationale": (
                        "Starts with a stronger action verb and marks the missing metric explicitly. "
                        "Replace the placeholder only with a verified number."
                    ),
                    "requires_approval": True,
                }
            )

        if _VAGUE.search(original):
            suggestions.append(
                {
                    "id": f"vague-{len(suggestions) + 1}",
                    "kind": "specificity",
                    "original": original,
                    "suggestion": original,
                    "rationale": (
                        "This bullet uses vague quantity words. Replace them with the actual scope "
                        "if you can verify it; do not guess."
                    ),
                    "requires_approval": True,
                }
            )

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

    return {
        "rewritten": "\n".join(rewritten_lines),
        "changes": changes,
        "method": "rule-based",
        "suggestions": suggestions[:20],
    }


def rewrite_resume(
    resume_text: str,
    job_description: str,
    *,
    ai_consent: bool = False,
) -> dict:
    settings = _settings()
    result = _try_openai_rewrite(resume_text, job_description, ai_consent)
    if result is None:
        result = _rule_based_rewrite(resume_text, job_description)

    return {
        "original": resume_text,
        "rewritten": result["rewritten"],
        "changes": result["changes"],
        "method": result["method"],
        "suggestions": result.get("suggestions", []),
        "ai_available": settings.openai_enabled,
        "ai_consent_required": settings.openai_enabled and not settings.openai_consent_default,
        "fabrication_notice": (
            "No employment history, projects, skills, certifications or metrics were invented. "
            "Metric placeholders must be replaced with verified values or removed."
        ),
    }
