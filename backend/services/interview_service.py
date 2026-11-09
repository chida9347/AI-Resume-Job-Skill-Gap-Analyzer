"""Interview question generation and heuristic mock-answer feedback.

Question selection is deterministic and grounded in the supplied role, skills
and resume projects. Nothing about the candidate is invented: project questions
only reference project titles and technologies that were extracted from the
resume.

The answer evaluator is a keyword/concept heuristic. It measures whether an
answer addresses the question and names the expected concepts. It is explicitly
*not* equivalent to a human interviewer's judgement.
"""

from __future__ import annotations

import re

from services.skill_taxonomy import DISPLAY_NAMES, category_of
from services.text_utils import STOPWORDS, split_sentences, tokenize

CATEGORY_ORDER = [
    "Programming fundamentals",
    "Data structures and algorithms",
    "Object-oriented programming",
    "DBMS and SQL",
    "Operating systems",
    "Computer networks",
    "Machine learning",
    "Deep learning",
    "Backend engineering",
    "Project-specific",
    "Behavioral",
]

_CATEGORY_BY_SKILL_CATEGORY = {
    "Programming Languages": "Programming fundamentals",
    "Frontend": "Programming fundamentals",
    "Backend": "Backend engineering",
    "Databases": "DBMS and SQL",
    "Cloud & DevOps": "Backend engineering",
    "Data & ML": "Machine learning",
    "Testing & Security": "Backend engineering",
    "CS Fundamentals": "Data structures and algorithms",
    "Tools & Practices": "Backend engineering",
    "Soft Skills": "Behavioral",
    "Business & Product": "Behavioral",
}

_SKILL_QUESTIONS: dict[str, list[dict]] = {
    "python": [
        {
            "category": "Programming fundamentals",
            "question": "What is the difference between a list and a tuple in Python, and when would you choose each?",
            "concepts": ["mutable", "immutable", "hashable", "performance", "dictionary key"],
        },
        {
            "category": "Programming fundamentals",
            "question": "How does Python's garbage collection work, and what practical problems can reference cycles cause?",
            "concepts": ["reference counting", "garbage collector", "cycle", "memory", "gc module"],
        },
    ],
    "javascript": [
        {
            "category": "Programming fundamentals",
            "question": "Explain event-loop ordering between the call stack, microtasks and macrotasks.",
            "concepts": ["call stack", "microtask", "macrotask", "promise", "setTimeout"],
        },
        {
            "category": "Programming fundamentals",
            "question": "What is the difference between `==` and `===`, and why does it matter?",
            "concepts": ["type coercion", "strict equality", "undefined", "null"],
        },
    ],
    "sql": [
        {
            "category": "DBMS and SQL",
            "question": "Walk through the difference between an INNER JOIN, a LEFT JOIN and a FULL OUTER JOIN with an example.",
            "concepts": ["inner join", "left join", "outer join", "null", "matching rows"],
        },
        {
            "category": "DBMS and SQL",
            "question": "How would you investigate and improve a slow query?",
            "concepts": ["explain plan", "index", "scan", "cardinality", "measure"],
        },
    ],
    "postgresql": [
        {
            "category": "DBMS and SQL",
            "question": "When would you add an index in PostgreSQL, and what costs does it introduce?",
            "concepts": ["selectivity", "write cost", "storage", "query plan", "composite index"],
        }
    ],
    "react": [
        {
            "category": "Programming fundamentals",
            "question": "Explain how React decides what to re-render and how you would avoid unnecessary renders.",
            "concepts": ["state", "props", "reconciliation", "memo", "key"],
        },
        {
            "category": "Programming fundamentals",
            "question": "What problem do React hooks solve, and what are the rules for using them?",
            "concepts": ["state", "side effect", "top level", "dependency array", "custom hook"],
        },
    ],
    "docker": [
        {
            "category": "Backend engineering",
            "question": "What is the difference between an image and a container, and how would you keep an image small?",
            "concepts": ["image", "container", "layer", "multi-stage build", "base image"],
        }
    ],
    "kubernetes": [
        {
            "category": "Backend engineering",
            "question": "How do liveness and readiness probes differ, and what happens when each fails?",
            "concepts": ["liveness", "readiness", "restart", "traffic", "probe"],
        }
    ],
    "machine learning": [
        {
            "category": "Machine learning",
            "question": "How do you detect overfitting, and what would you change if you found it?",
            "concepts": ["train validation gap", "regularisation", "more data", "cross validation", "complexity"],
        },
        {
            "category": "Machine learning",
            "question": "Why is accuracy a poor metric for an imbalanced classification problem?",
            "concepts": ["class imbalance", "precision", "recall", "f1", "confusion matrix"],
        },
    ],
    "deep learning": [
        {
            "category": "Deep learning",
            "question": "What problem does batch normalisation address, and what are its trade-offs?",
            "concepts": ["internal covariate shift", "normalisation", "batch size", "training stability"],
        }
    ],
    "data structures": [
        {
            "category": "Data structures and algorithms",
            "question": "Compare an array and a hash map for lookup, insertion and memory use.",
            "concepts": ["constant time", "collision", "contiguous memory", "worst case", "resize"],
        }
    ],
    "algorithms": [
        {
            "category": "Data structures and algorithms",
            "question": "How do you decide between a greedy approach and dynamic programming?",
            "concepts": ["optimal substructure", "overlapping subproblems", "counterexample", "complexity"],
        }
    ],
    "object-oriented programming": [
        {
            "category": "Object-oriented programming",
            "question": "Explain the difference between inheritance and composition, with a reason to prefer one.",
            "concepts": ["inheritance", "composition", "coupling", "reuse", "flexibility"],
        }
    ],
    "operating systems": [
        {
            "category": "Operating systems",
            "question": "What is the difference between a process and a thread, and what does each share?",
            "concepts": ["address space", "thread", "process", "shared memory", "context switch"],
        }
    ],
    "computer networks": [
        {
            "category": "Computer networks",
            "question": "What happens between typing a URL and the browser receiving a response?",
            "concepts": ["dns", "tcp", "tls", "http", "response"],
        }
    ],
    "http": [
        {
            "category": "Computer networks",
            "question": "Which HTTP status codes do you use for validation errors, authentication failures and server errors?",
            "concepts": ["400", "401", "403", "422", "500"],
        }
    ],
    "rest apis": [
        {
            "category": "Backend engineering",
            "question": "What makes an API RESTful, and where does that model become awkward?",
            "concepts": ["resources", "stateless", "http verbs", "status codes", "idempotency"],
        }
    ],
    "authentication": [
        {
            "category": "Backend engineering",
            "question": "Compare session-based authentication with JWT access tokens. What are the revocation trade-offs?",
            "concepts": ["session", "jwt", "stateless", "revocation", "expiry"],
        }
    ],
}

_ROLE_QUESTIONS = [
    {
        "category": "Behavioral",
        "question": "Tell me about a project you are proud of. What was your specific contribution and what would you do differently?",
        "concepts": ["situation", "action", "result", "contribution", "learning"],
    },
    {
        "category": "Behavioral",
        "question": "Describe a time you disagreed with a teammate. How did you resolve it?",
        "concepts": ["situation", "disagreement", "listened", "resolution", "outcome"],
    },
    {
        "category": "Behavioral",
        "question": "Tell me about a bug that was hard to diagnose. How did you find the root cause?",
        "concepts": ["symptom", "hypothesis", "investigation", "root cause", "prevention"],
    },
    {
        "category": "Behavioral",
        "question": "How do you prioritise when you have more work than time?",
        "concepts": ["impact", "deadline", "communication", "trade-off", "prioritisation"],
    },
]

_PROJECT_QUESTION_TEMPLATES = [
    "Walk me through {title}. What problem did it solve, what did you build, and how did you verify it worked?",
    "What was the hardest technical decision in {title}, and what alternatives did you consider?",
    "If {title} had to handle ten times the load, what would you change first?",
]

_TIPS = [
    "Use a specific situation, the action you took, and the observable result.",
    "State your own contribution instead of describing the team's work.",
    "Name the trade-off you considered; interviewers look for reasoning, not only the answer.",
    "If you do not know something, say so and describe how you would find out.",
    "Keep answers to roughly two minutes, then invite a follow-up question.",
]


def _display(skill: str) -> str:
    return DISPLAY_NAMES.get(skill.casefold(), skill)


def _skill_question(skill: str) -> dict:
    key = skill.casefold()
    bank = _SKILL_QUESTIONS.get(key)
    if bank:
        chosen = bank[0]
        return {
            "category": chosen["category"],
            "question": chosen["question"],
            "concepts": chosen["concepts"],
            "difficulty": "intermediate",
        }
    display = _display(key)
    category = _CATEGORY_BY_SKILL_CATEGORY.get(category_of(key), "Backend engineering")
    return {
        "category": category,
        "question": (
            f"Explain how you have used {display} in practice. What problem did it solve, "
            "what trade-offs did you make, and how did you verify the result?"
        ),
        "concepts": [display.lower(), "problem", "trade-off", "verification", "result"],
        "difficulty": "intermediate",
    }


def _project_questions(projects: list[dict], limit: int = 3) -> list[dict]:
    questions: list[dict] = []
    for index, project in enumerate(projects[:limit]):
        title = str(project.get("title") or "").strip()
        if not title:
            continue
        technologies = [
            _display(str(skill)) for skill in project.get("technologies", [])[:3] if skill
        ]
        template = _PROJECT_QUESTION_TEMPLATES[index % len(_PROJECT_QUESTION_TEMPLATES)]
        concepts = [word.lower() for word in title.split() if len(word) > 3][:3]
        concepts.extend(skill.casefold() for skill in technologies)
        questions.append(
            {
                "category": "Project-specific",
                "question": template.format(title=title),
                "concepts": concepts or ["problem", "contribution", "result"],
                "difficulty": "intermediate",
                "related_skill": "",
                "source": "project",
                "project": title,
                "technologies": technologies,
            }
        )
    return questions


def generate_interview_questions(
    role: str = "",
    *,
    required_skills: list[str] | None = None,
    missing_skills: list[str] | None = None,
    resume_skills: list[str] | None = None,
    projects: list[dict] | None = None,
    limit: int = 15,
) -> dict:
    required_skills = [skill for skill in (required_skills or []) if skill]
    missing_skills = [skill for skill in (missing_skills or []) if skill]
    resume_skills = [skill for skill in (resume_skills or []) if skill]
    projects = projects or []

    role_label = (role or "").strip() or "the target role"
    questions: list[dict] = []
    seen_questions: set[str] = set()

    def add(entry: dict, source: str, related_skill: str = "") -> None:
        question = entry["question"].strip()
        if question.casefold() in seen_questions:
            return
        seen_questions.add(question.casefold())
        questions.append(
            {
                "id": f"q{len(questions) + 1}",
                "category": entry["category"],
                "question": question,
                "difficulty": entry.get("difficulty", "intermediate"),
                "related_skill": related_skill,
                "source": source,
                "why": (
                    f"The posting names {_display(related_skill)} as relevant."
                    if related_skill and source == "skill"
                    else "This checks reasoning that the role or resume makes relevant."
                ),
                "answer_framework": (
                    "Use a concrete situation, explain your action and the trade-off, "
                    "then state the result and what you learned."
                ),
                "expected_concepts": entry.get("concepts", []),
                "project": entry.get("project", ""),
                "technologies": entry.get("technologies", []),
            }
        )

    # 1. Missing skills first: these are the most useful preparation.
    for skill in missing_skills[:4]:
        add(_skill_question(skill), "skill", skill)

    # 2. Required skills, avoiding duplicates already covered.
    covered = {skill.casefold() for skill in missing_skills[:4]}
    for skill in required_skills:
        if skill.casefold() in covered:
            continue
        add(_skill_question(skill), "skill", skill)
        covered.add(skill.casefold())
        if len([item for item in questions if item["source"] == "skill"]) >= 6:
            break

    # 3. Resume skills that the posting did not mention still deserve a check.
    for skill in resume_skills:
        if len([item for item in questions if item["source"] == "skill"]) >= 7:
            break
        if skill.casefold() in covered:
            continue
        add(_skill_question(skill), "skill", skill)
        covered.add(skill.casefold())

    # 4. Project-specific questions grounded in extracted projects.
    for entry in _project_questions(projects):
        add(entry, "project")

    # 5. Role and behavioural questions.
    for entry in _ROLE_QUESTIONS:
        add(entry, "behavioral")

    questions = questions[:limit]
    return {
        "role": role_label,
        "questions": questions,
        "tips": _TIPS,
        "categories": list(dict.fromkeys(item["category"] for item in questions)),
        "method": "deterministic-grounded",
        "disclaimer": (
            "Questions are generated from the role, skills and projects you provided. "
            "They are practice prompts, not the questions an employer will ask."
        ),
    }


def _concept_present(concept: str, answer_tokens: set[str], answer_lower: str) -> bool:
    concept_lower = concept.casefold()
    if concept_lower in answer_lower:
        return True
    concept_tokens = [token for token in tokenize(concept) if token not in STOPWORDS]
    if not concept_tokens:
        return False
    return all(token in answer_tokens for token in concept_tokens)


def evaluate_answer(question: str, answer: str, expected_concepts: list[str] | None = None) -> dict:
    """Heuristic answer feedback.

    This is a transparent coverage check, not a semantic grader. It rewards
    addressing the question, naming expected concepts, giving concrete detail
    and keeping the answer to a reasonable length.
    """
    answer = (answer or "").strip()
    expected_concepts = [concept for concept in (expected_concepts or []) if concept]
    if not expected_concepts:
        expected_concepts = [
            token for token in tokenize(question) if token not in STOPWORDS and len(token) > 3
        ][:6]

    answer_tokens = set(tokenize(answer))
    answer_lower = answer.casefold()
    covered = [concept for concept in expected_concepts if _concept_present(concept, answer_tokens, answer_lower)]
    missing = [concept for concept in expected_concepts if concept not in covered]

    word_count = len(answer.split())
    relevance = round(len(covered) / len(expected_concepts) * 100) if expected_concepts else 0

    # Length is a signal, not a goal: very short answers cannot demonstrate reasoning.
    length_score = 100 if 60 <= word_count <= 320 else 70 if 30 <= word_count < 60 else 40 if word_count else 0
    if word_count > 320:
        length_score = 60

    has_specifics = bool(
        re.search(r"\b\d+(?:\.\d+)?\s?(?:%|ms|s|seconds|minutes|users|requests|records|rows|hours|days)\b", answer, re.I)
        or re.search(r"\b(?:because|therefore|trade-?off|instead|result|measured|verified)\b", answer, re.I)
    )
    specificity = 100 if has_specifics else 50 if word_count >= 40 else 20

    structure = 100 if re.search(r"\b(?:first|then|finally|result|outcome|learned)\b", answer, re.I) else 60
    if not answer:
        structure = 0

    score = round(relevance * 0.5 + length_score * 0.15 + specificity * 0.2 + structure * 0.15)

    strengths: list[str] = []
    improvements: list[str] = []
    if covered:
        strengths.append("Addresses these expected concepts: " + ", ".join(covered[:6]) + ".")
    if has_specifics:
        strengths.append("Includes concrete detail or explicit reasoning rather than only definitions.")
    if 60 <= word_count <= 320:
        strengths.append("Answer length is appropriate for a spoken response.")
    if not answer:
        improvements.append("No answer was provided. Write the answer you would give aloud.")
    elif relevance < 50:
        improvements.append("Address the question more directly; name the core concepts it asks about.")
    if missing:
        improvements.append("Consider discussing: " + ", ".join(missing[:6]) + ".")
    if word_count < 40:
        improvements.append("Add a concrete example or the reasoning behind your choice.")
    if word_count > 320:
        improvements.append("Tighten the answer to the key decision, action and result.")
    if not has_specifics:
        improvements.append("Add a specific trade-off, measurement or verified result if you have one.")
    if not improvements:
        improvements.append("Structure the answer as situation, action, result and learning.")

    return {
        "score": max(0, min(100, score)),
        "relevance": relevance,
        "covered_concepts": covered,
        "missing_concepts": missing,
        "word_count": word_count,
        "strengths": strengths,
        "improvements": improvements,
        "feedback": (
            "This is an automated coverage estimate based on expected concepts. "
            "It cannot judge correctness, depth or delivery like a human interviewer."
        ),
        "method": "heuristic-concept-coverage",
        "disclaimer": (
            "Automated feedback is not equivalent to a real interviewer's judgement "
            "and should be used only for practice."
        ),
    }


def summarize_session(answers: list[dict]) -> dict:
    """Aggregate mock-interview attempts without inventing a pass/fail claim."""
    if not answers:
        return {
            "attempts": 0,
            "average_score": 0,
            "strongest_category": "",
            "weakest_category": "",
            "summary": "No answers have been recorded yet.",
        }
    scores = [int(item.get("score", 0)) for item in answers]
    by_category: dict[str, list[int]] = {}
    for item in answers:
        by_category.setdefault(str(item.get("category", "General")), []).append(int(item.get("score", 0)))
    averages = {category: sum(values) / len(values) for category, values in by_category.items()}
    strongest = max(averages, key=averages.get)
    weakest = min(averages, key=averages.get)
    return {
        "attempts": len(answers),
        "average_score": round(sum(scores) / len(scores)),
        "strongest_category": strongest,
        "weakest_category": weakest,
        "by_category": {category: round(value) for category, value in averages.items()},
        "summary": (
            f"You answered {len(answers)} question(s) with an average coverage score of "
            f"{round(sum(scores) / len(scores))}. Revisit {weakest} next."
        ),
        "disclaimer": "Scores measure concept coverage only, not interview readiness.",
    }
