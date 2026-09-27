import re
from functools import lru_cache
from typing import Iterable


SKILLS = {
    "python": ["python"],
    "javascript": ["javascript"],
    "typescript": ["typescript", "ts"],
    "react": ["react", "react.js", "reactjs"],
    "node.js": ["node.js", "nodejs", "node js"],
    "fastapi": ["fastapi"],
    "sql": ["sql", "postgresql", "mysql", "sqlite"],
    "aws": ["aws", "amazon web services"],
    "azure": ["azure"],
    "gcp": ["gcp", "google cloud"],
    "docker": ["docker", "containerization"],
    "kubernetes": ["kubernetes", "k8s"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning"],
    "nlp": ["natural language processing", "nlp"],
    "data analysis": ["data analysis", "data analytics"],
    "data visualization": ["data visualization", "tableau", "power bi"],
    "excel": ["excel", "spreadsheets"],
    "git": ["git", "github", "gitlab"],
    "ci/cd": ["ci/cd", "continuous integration", "continuous deployment"],
    "rest apis": ["rest api", "restful api", "rest apis"],
    "graphql": ["graphql"],
    "html": ["html", "html5"],
    "css": ["css", "css3", "tailwind", "sass"],
    "java": ["java"],
    "c++": ["c++"],
    "c#": ["c#", "c sharp"],
    ".net": [".net", "dotnet"],
    "go": ["golang", " go "],
    "rust": ["rust"],
    "linux": ["linux", "unix"],
    "agile": ["agile", "scrum", "kanban"],
    "project management": ["project management", "program management"],
    "communication": ["communication", "stakeholder management"],
    "leadership": ["leadership", "team leadership", "mentoring"],
    "testing": ["testing", "unit tests", "pytest", "jest"],
    "security": ["security", "owasp", "authentication"],
    "pytorch": ["pytorch"],
    "tensorflow": ["tensorflow"],
    "pandas": ["pandas"],
    "spark": ["apache spark", "pyspark", "spark"],
}


def _contains_phrase(text: str, phrase: str) -> bool:
    pattern = r"(?<![a-z0-9])" + re.escape(phrase.strip()) + r"(?![a-z0-9])"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


@lru_cache(maxsize=1)
def _skill_matcher():
    try:
        import spacy
        from spacy.matcher import PhraseMatcher

        nlp = spacy.blank("en")
        matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
        for skill, aliases in SKILLS.items():
            matcher.add(skill, [nlp.make_doc(alias) for alias in aliases])
        return nlp, matcher
    except Exception:
        return None


def extract_skills(text: str) -> list[str]:
    skill_matcher = _skill_matcher()
    if skill_matcher and len(text) < skill_matcher[0].max_length:
        nlp, matcher = skill_matcher
        document = nlp.make_doc(text)
        found = {nlp.vocab.strings[match_id] for match_id, _, _ in matcher(document)}
        return [skill for skill in SKILLS if skill in found]

    normalized = f" {text.lower()} "
    return [
        skill
        for skill, aliases in SKILLS.items()
        if any(_contains_phrase(normalized, alias) for alias in aliases)
    ]


@lru_cache(maxsize=1)
def _embedding_model():
    try:
        from sentence_transformers import SentenceTransformer

        # Local-only loading avoids unexpected downloads or network access.
        return SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
    except Exception:
        return None


def _semantic_pairs(missing: Iterable[str], resume_skills: Iterable[str]) -> set[str]:
    model = _embedding_model()
    if model is None:
        return set()

    try:
        from sentence_transformers import util

        missing_list, resume_list = list(missing), list(resume_skills)
        if not missing_list or not resume_list:
            return set()
        scores = util.cos_sim(model.encode(missing_list), model.encode(resume_list))
        return {
            skill
            for index, skill in enumerate(missing_list)
            if float(scores[index].max()) >= 0.78
        }
    except Exception:
        return set()


def compare_skills(resume_skills: list[str], job_skills: list[str]) -> dict:
    resume_set = {skill.lower() for skill in resume_skills}
    required = list(dict.fromkeys(skill.lower() for skill in job_skills))
    matched = [skill for skill in required if skill in resume_set]
    unmatched = [skill for skill in required if skill not in resume_set]
    semantic_matches = _semantic_pairs(unmatched, resume_set)
    matched.extend(skill for skill in unmatched if skill in semantic_matches)
    missing = [skill for skill in unmatched if skill not in semantic_matches]
    score = round(len(matched) / len(required) * 100) if required else 0
    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "similarity_score": score,
        "ats_score": score,
    }


def make_suggestions(missing_skills: list[str], resume_text: str) -> list[dict]:
    suggestions = []
    for skill in missing_skills[:8]:
        suggestions.append({
            "id": skill,
            "skill": skill,
            "kind": "skill",
            "text": f"I have this skill; add {skill} to my resume Skills section.",
            "accepted": False,
        })
    if resume_text and len(resume_text.split()) < 180:
        suggestions.append({
            "id": "add-detail",
            "skill": "More detail",
            "kind": "review",
            "text": "Add measurable outcomes, scope, and context to your strongest experience.",
            "accepted": False,
        })
    return suggestions


_SKILLS_HEADING = re.compile(r"^\s*(?:technical\s+)?skills\s*:?\s*$", re.IGNORECASE)
_INLINE_SKILLS_HEADING = re.compile(r"^(\s*(?:technical\s+)?skills\s*:\s*)(.*)$", re.IGNORECASE)
_RESUME_SECTION_HEADING = re.compile(
    r"^\s*(?:summary|profile|objective|professional\s+)?(?:experience|employment\s+history|work\s+history|education|skills|technical\s+skills|projects?|certifications?|volunteer|awards?)\s*:?\s*$",
    re.IGNORECASE,
)
_SKILL_DISPLAY_NAMES = {
    "aws": "AWS",
    "c#": "C#",
    "c++": "C++",
    "ci/cd": "CI/CD",
    ".net": ".NET",
    "gcp": "GCP",
    "javascript": "JavaScript",
    "kubernetes": "Kubernetes",
    "nlp": "NLP",
    "node.js": "Node.js",
    "rest apis": "REST APIs",
    "sql": "SQL",
    "typescript": "TypeScript",
}


def _contains_skill_phrase(text: str, skill: str) -> bool:
    pattern = r"(?<![a-z0-9])" + re.escape(skill.strip()) + r"(?![a-z0-9])"
    return re.search(pattern, text, re.IGNORECASE) is not None


def _insert_confirmed_skills(resume_text: str, accepted_skills: list[str]) -> str:
    skills = list(dict.fromkeys(
        _SKILL_DISPLAY_NAMES.get(skill.strip().casefold(), skill.strip().title())
        for skill in accepted_skills
        if skill.strip() and len(skill.strip()) <= 80 and not re.search(r"[\r\n]", skill)
    ))
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
    role_name = role.strip() or "this role"
    return {
        "role": role_name,
        "questions": [
            {
                "question": f"What experience makes you a strong fit for {role_name}?",
                "example_answer": "Connect one relevant project to the role's needs. Explain your contribution, the decisions you made, and the measurable result. Replace this framework with your own experience.",
            },
            {
                "question": "Tell me about a challenging problem you solved.",
                "example_answer": "Use the STAR structure: describe the situation and task, explain the actions you personally took, then share the outcome and what you learned.",
            },
            {
                "question": "How do you approach learning an unfamiliar tool or skill?",
                "example_answer": "Give a real example. Walk through how you broke the learning into steps, tested your understanding, and applied it to a practical problem.",
            },
        ],
        "tips": [
            "Prepare two concise project stories with specific outcomes.",
            "Use examples that distinguish your contribution from the team's work.",
            "Be candid about gaps and explain how you would close them.",
        ],
    }