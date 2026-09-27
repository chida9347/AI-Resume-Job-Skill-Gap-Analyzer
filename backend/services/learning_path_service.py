from typing import TypedDict


class _LearningPlan(TypedDict):
    roadmap: list[str]
    project: str
    duration: str


_PLANS: dict[str, _LearningPlan] = {
    "docker": {
        "roadmap": [
            "Learn images, containers, registries, and the Docker CLI.",
            "Write a Dockerfile and build a small application image.",
            "Add environment configuration, health checks, and persistent storage.",
            "Run a multi-service setup with Docker Compose and document the workflow.",
        ],
        "project": "Containerize a small API with a database and a reproducible Compose setup.",
        "duration": "5 days",
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
    },
}


def generate_learning_paths(missing_skills: list[str]) -> list[dict]:
    paths = []
    seen: set[str] = set()
    for raw_skill in missing_skills:
        skill = raw_skill.strip()
        normalized = skill.casefold()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        plan = _PLANS.get(normalized, {
            "roadmap": [
                f"Clarify the core concepts and vocabulary of {skill}.",
                f"Complete a small guided exercise using {skill}.",
                f"Apply {skill} to a realistic task related to your target role.",
                "Review the result, identify gaps, and document what you learned.",
            ],
            "project": f"Create a small, documented project that demonstrates practical use of {skill}.",
            "duration": "5 days",
        })
        paths.append({"skill": skill, **plan})
    return paths