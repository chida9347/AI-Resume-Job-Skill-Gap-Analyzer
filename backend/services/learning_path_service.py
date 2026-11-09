"""Personalised, stage-based learning roadmaps.

Plans are generated only for skills the analysis marked as missing or partial.
Each plan keeps the original ``skill`` / ``roadmap`` / ``project`` /
``duration`` keys for API compatibility and adds objectives, concepts,
exercises, a level, a priority and a completion status for the UI.

No course links or endorsements are produced: the service cannot verify that a
third-party resource exists or is current.
"""

from __future__ import annotations

from services.skill_taxonomy import DISPLAY_NAMES, SKILL_BY_NAME, category_of

_PRIORITY_ORDER = {"required": 0, "preferred": 1, "mentioned": 2, "": 3}

# Category-level scaffolding. Skill-specific plans below override the practical
# steps when a more concrete sequence is known.
_CATEGORY_TEMPLATES: dict[str, dict] = {
    "Programming Languages": {
        "level": "beginner",
        "duration": "7 days",
        "objectives": [
            "Read and write idiomatic {skill} code without relying on copy-paste.",
            "Use the standard library and error handling correctly.",
            "Structure a small program into testable functions or modules.",
        ],
        "concepts": ["syntax and types", "control flow", "collections", "error handling", "modules and packaging"],
        "exercises": [
            "Solve five small parsing or data-transformation tasks in {skill}.",
            "Write unit tests for one function, including an edge case.",
            "Refactor a duplicated block into a reusable function.",
        ],
        "roadmap": [
            "Review {skill} syntax, types, collections and error handling.",
            "Write small programs that read, transform and validate real data.",
            "Add automated tests and debug one failing case deliberately.",
            "Package and document a small tool so another person can run it.",
        ],
        "project": "Build a tested {skill} command-line tool that transforms and validates a real dataset.",
    },
    "Frontend": {
        "level": "beginner",
        "duration": "7 days",
        "objectives": [
            "Build a responsive interface with accessible form controls.",
            "Manage component state and asynchronous data loading.",
            "Handle loading, empty and error states explicitly.",
        ],
        "concepts": ["components", "state and props", "events and forms", "async data", "accessibility", "responsive layout"],
        "exercises": [
            "Build a form with validation and an accessible error summary.",
            "Fetch a public API and render loading, empty and error states.",
            "Test keyboard navigation and a narrow viewport.",
        ],
        "roadmap": [
            "Review components, props, state and event handling in {skill}.",
            "Build controlled forms with clear validation states.",
            "Fetch API data and handle loading, empty and error states.",
            "Test keyboard access and responsive behaviour on a small screen.",
        ],
        "project": "Build an accessible dashboard with filters, async data and saved preferences.",
    },
    "Backend": {
        "level": "intermediate",
        "duration": "7 days",
        "objectives": [
            "Design and implement a small HTTP API with validated inputs.",
            "Handle authentication, errors and persistence safely.",
            "Document endpoints and test the happy and failure paths.",
        ],
        "concepts": ["HTTP semantics", "request validation", "routing", "error handling", "authentication", "database access"],
        "exercises": [
            "Implement CRUD endpoints with request validation.",
            "Add a consistent error response contract.",
            "Write integration tests for one success and two failure cases.",
        ],
        "roadmap": [
            "Review HTTP methods, status codes and resource modelling.",
            "Implement validated CRUD endpoints in {skill}.",
            "Add authentication, structured errors and database access.",
            "Write integration tests and document the API.",
        ],
        "project": "Build a small {skill} API with validation, tests and documented endpoints.",
    },
    "Databases": {
        "level": "beginner",
        "duration": "5 days",
        "objectives": [
            "Model related data with clear keys and constraints.",
            "Write correct queries for filtering, aggregation and joins.",
            "Explain the trade-offs of an index or schema change.",
        ],
        "concepts": ["schema design", "keys and constraints", "joins", "aggregation", "indexes", "query plans"],
        "exercises": [
            "Model a small multi-table schema for {skill}.",
            "Write three queries that answer real questions about the data.",
            "Inspect one query plan and justify an index.",
        ],
        "roadmap": [
            "Review the data model, keys and constraints for {skill}.",
            "Practice filtering, aggregation and multi-table joins.",
            "Use transactions and inspect query plans for one slow query.",
            "Document the schema and the reason for each index.",
        ],
        "project": "Model a realistic dataset in {skill}, document the schema and optimise one measured query.",
    },
    "Cloud & DevOps": {
        "level": "intermediate",
        "duration": "7 days",
        "objectives": [
            "Deploy a small service reproducibly with least-privilege access.",
            "Add health checks, logging and a rollback path.",
            "Explain cost and reliability trade-offs.",
        ],
        "concepts": ["containers", "CI/CD", "infrastructure as code", "least privilege", "observability", "rollbacks"],
        "exercises": [
            "Containerise or provision a small service with {skill}.",
            "Add a health check and a documented rollback.",
            "Review permissions and remove one unnecessary privilege.",
        ],
        "roadmap": [
            "Review the core concepts and vocabulary of {skill}.",
            "Deploy a small service with health checks and configuration.",
            "Add logging, least-privilege access and a rollback path.",
            "Estimate cost, tear down unused resources and document the workflow.",
        ],
        "project": "Deploy a small API with {skill}, a health endpoint, least-privilege access and a cost note.",
    },
    "Data & ML": {
        "level": "intermediate",
        "duration": "10 days",
        "objectives": [
            "Frame a problem and choose a defensible baseline.",
            "Evaluate results with metrics that match the task.",
            "Document limitations and failure cases honestly.",
        ],
        "concepts": ["problem framing", "data preparation", "baselines", "evaluation metrics", "overfitting", "limitations"],
        "exercises": [
            "Build a baseline and record its metrics on a held-out split.",
            "Compare {skill} against the baseline and explain the difference.",
            "Write a short limitations section with at least two failure cases.",
        ],
        "roadmap": [
            "Review the core theory and vocabulary of {skill}.",
            "Prepare a small dataset and build a reproducible baseline.",
            "Apply {skill} and evaluate with appropriate metrics.",
            "Document results, limitations and the next experiment.",
        ],
        "project": "Complete a small {skill} study with a baseline, honest metrics and documented limitations.",
    },
    "Testing & Security": {
        "level": "intermediate",
        "duration": "5 days",
        "objectives": [
            "Write tests that fail for the right reason.",
            "Identify and fix a realistic weakness in a small application.",
            "Explain the threat model behind a mitigation.",
        ],
        "concepts": ["test design", "edge cases", "threat modelling", "input validation", "least privilege", "regression tests"],
        "exercises": [
            "Write a failing test, then make it pass without weakening it.",
            "Find and fix one input-validation weakness.",
            "Add a regression test for the fixed issue.",
        ],
        "roadmap": [
            "Review the purpose and limits of {skill}.",
            "Write tests or checks for one realistic failure case.",
            "Apply the practice to a small application and record the result.",
            "Document the remaining risks and how they would be monitored.",
        ],
        "project": "Harden a small application with {skill} and document the tests and remaining risks.",
    },
    "CS Fundamentals": {
        "level": "beginner",
        "duration": "10 days",
        "objectives": [
            "Explain the core idea of {skill} in plain language.",
            "Choose an appropriate data structure or algorithm for a task.",
            "Analyse time and space complexity.",
        ],
        "concepts": ["complexity analysis", "core data structures", "problem decomposition", "trade-offs", "correctness"],
        "exercises": [
            "Solve five practice problems and state the complexity of each.",
            "Compare two approaches to the same problem and justify a choice.",
            "Explain one solution aloud as you would in an interview.",
        ],
        "roadmap": [
            "Review the core vocabulary and rules of {skill}.",
            "Work through small problems with explicit complexity analysis.",
            "Compare alternative approaches and justify a choice.",
            "Practice explaining solutions clearly and concisely.",
        ],
        "project": "Build a small reference implementation that demonstrates {skill} with tests and complexity notes.",
    },
    "Tools & Practices": {
        "level": "beginner",
        "duration": "4 days",
        "objectives": [
            "Use {skill} in a repeatable, documented workflow.",
            "Recognise the failure modes the tool or practice prevents.",
            "Integrate it into an existing small project.",
        ],
        "concepts": ["core workflow", "configuration", "common failure modes", "automation", "documentation"],
        "exercises": [
            "Apply {skill} to an existing small project.",
            "Document the setup steps so another person can repeat them.",
            "Identify one failure mode and how the workflow catches it.",
        ],
        "roadmap": [
            "Review what {skill} is for and when it is appropriate.",
            "Apply it to a small project with a documented setup.",
            "Identify and resolve one realistic failure.",
            "Write a short runbook for future use.",
        ],
        "project": "Integrate {skill} into a small project and document the setup and failure handling.",
    },
    "Soft Skills": {
        "level": "beginner",
        "duration": "5 days",
        "objectives": [
            "Describe a concrete situation where {skill} mattered.",
            "Explain the action you took and the observable result.",
            "Practise a concise, honest answer for an interview.",
        ],
        "concepts": ["situation-action-result", "specific examples", "self-awareness", "feedback", "impact"],
        "exercises": [
            "Write two STAR stories that demonstrate {skill}.",
            "Ask a peer or mentor for specific feedback on one story.",
            "Record a two-minute answer and remove filler.",
        ],
        "roadmap": [
            "Identify two real situations that demonstrate {skill}.",
            "Write them as situation, action and result stories.",
            "Get feedback and tighten the wording.",
            "Rehearse a two-minute spoken version.",
        ],
        "project": "Prepare three evidence-based STAR stories that demonstrate {skill} without exaggeration.",
    },
}

_SKILL_PLANS: dict[str, dict] = {
    "docker": {
        "roadmap": [
            "Learn images, containers, registries, and the Docker CLI.",
            "Write a Dockerfile and build a small application image.",
            "Add environment configuration, health checks, and persistent storage.",
            "Run a multi-service setup with Docker Compose and document the workflow.",
        ],
        "project": "Containerize a small API with a database and a reproducible Compose setup.",
        "duration": "5 days",
        "level": "beginner",
    },
    "kubernetes": {
        "roadmap": [
            "Learn pods, deployments, services, and namespaces.",
            "Deploy a containerized application to a local cluster.",
            "Configure probes, resource requests, and secrets.",
            "Roll out an update and verify recovery from a failed pod.",
        ],
        "project": "Deploy a small web app with health checks and a documented rollout.",
        "duration": "7 days",
        "level": "intermediate",
    },
    "sql": {
        "roadmap": [
            "Practice filtering, sorting, and aggregation with SELECT queries.",
            "Model related tables and write joins with clear keys.",
            "Use CTEs and window functions to answer multi-step questions.",
            "Inspect query plans and improve one measured slow query.",
        ],
        "project": "Analyze a public dataset and document queries, findings, and one query optimization.",
        "duration": "5 days",
        "level": "beginner",
    },
    "python": {
        "roadmap": [
            "Review core syntax, collections, functions, and exceptions.",
            "Structure a small project into modules with clear interfaces.",
            "Add automated tests and use a debugger to resolve a defect.",
            "Document setup and package the project for repeatable use.",
        ],
        "project": "Build a tested command-line tool that transforms and validates a real dataset.",
        "duration": "7 days",
        "level": "beginner",
    },
    "react": {
        "roadmap": [
            "Practice components, props, state, and event handling.",
            "Build forms with controlled inputs and clear validation states.",
            "Fetch API data and handle loading, empty, and error states.",
            "Test keyboard access and responsive behavior on a small screen.",
        ],
        "project": "Build an accessible job-search dashboard with filters and saved roles.",
        "duration": "7 days",
        "level": "beginner",
    },
    "aws": {
        "roadmap": [
            "Learn IAM roles, policies, regions, and basic networking concepts.",
            "Deploy a small service using a managed compute option.",
            "Add logging, health monitoring, and a least-privilege role.",
            "Estimate costs and tear down unused resources.",
        ],
        "project": "Deploy a small API with a health endpoint, least-privilege access, and a cost note.",
        "duration": "7 days",
        "level": "intermediate",
    },
}


def _display(skill: str) -> str:
    return DISPLAY_NAMES.get(skill.casefold(), skill)


def _template_for(skill: str) -> dict:
    category = category_of(skill.casefold())
    template = _CATEGORY_TEMPLATES.get(category) or {
        "level": "beginner",
        "duration": "5 days",
        "objectives": [
            "Explain the core concepts and vocabulary of {skill}.",
            "Complete a small guided exercise using {skill}.",
            "Apply {skill} to a realistic task related to your target role.",
        ],
        "concepts": ["core concepts", "common workflows", "typical failure modes"],
        "exercises": [
            "Complete one guided exercise using {skill}.",
            "Apply {skill} to a small task and document the result.",
        ],
        "roadmap": [
            "Clarify the core concepts and vocabulary of {skill}.",
            "Complete a small guided exercise using {skill}.",
            "Apply {skill} to a realistic task related to your target role.",
            "Review the result, identify gaps, and document what you learned.",
        ],
        "project": "Create a small, documented project that demonstrates practical use of {skill}.",
    }
    merged = {**template, **_SKILL_PLANS.get(skill.casefold(), {})}
    return merged


def _priority(skill: str, index: int, requirement: str) -> str:
    level = _PRIORITY_ORDER.get(requirement, 3)
    if level == 0 and index < 3:
        return "high"
    if level <= 1 and index < 6:
        return "medium"
    return "low"


def _evidence_level(evidence: dict | None, skill: str) -> str:
    if not evidence:
        return "missing"
    entry = evidence.get(skill.casefold())
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        return str(entry.get("status") or entry.get("strength") or "missing")
    return "missing"


def generate_learning_paths(
    missing_skills: list[str],
    *,
    evidence: dict | None = None,
    requirements: dict | None = None,
) -> list[dict]:
    """Build a plan per missing skill.

    ``evidence`` maps a skill to a status (strong / mentioned / partial /
    missing) and ``requirements`` maps a skill to required / preferred. Both are
    optional so the legacy ``{"missing_skills": [...]}`` request still works.
    """
    evidence = evidence or {}
    requirements = requirements or {}
    paths: list[dict] = []
    seen: set[str] = set()

    for index, raw_skill in enumerate(missing_skills):
        skill = raw_skill.strip()
        if not skill:
            continue
        normalized = skill.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)

        display = _display(skill)
        template = _template_for(normalized)
        requirement = requirements.get(normalized, "")
        roadmap = [step.format(skill=display) for step in template["roadmap"]][:4]
        if len(roadmap) < 3:
            roadmap.append(f"Review the result and document what you learned about {display}.")

        paths.append(
            {
                "skill": skill,
                "display": display,
                "category": category_of(normalized),
                "level": template.get("level", "beginner"),
                "priority": _priority(normalized, index, requirement),
                "requirement": requirement or "missing",
                "current_evidence": _evidence_level(evidence, normalized),
                "roadmap": roadmap,
                "objectives": [
                    objective.format(skill=display) for objective in template.get("objectives", [])
                ],
                "concepts": [
                    concept.format(skill=display) for concept in template.get("concepts", [])
                ],
                "exercises": [
                    exercise.format(skill=display) for exercise in template.get("exercises", [])
                ],
                "stages": [
                    {
                        "order": position + 1,
                        "title": step,
                        "status": "not_started",
                    }
                    for position, step in enumerate(roadmap)
                ],
                "project": template["project"].format(skill=display),
                "duration": template.get("duration", "5 days"),
                "completion_status": "not_started",
                "progress": 0,
                "note": (
                    "This plan is generated from the skills the analysis marked as missing. "
                    "It is a suggested sequence, not a certification or course."
                ),
            }
        )

    return paths
