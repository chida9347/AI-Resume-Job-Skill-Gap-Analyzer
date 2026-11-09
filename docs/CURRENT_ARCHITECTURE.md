# Current Architecture

## Runtime topology

```text
Browser (React 19 + Vite)
        |
        | JSON / multipart over HTTP (Axios)
        v
FastAPI (uvicorn)
  routes/          request validation, HTTP concerns
  services/        parsing, taxonomy, matching, scoring, rewriting, roadmaps, interviews
  models/schemas   Pydantic request/response contracts
  SQLAlchemy       users, resumes, jobs, analyses, interviews (optional auth flow)
        |
        +--> SQLite (local default) / PostgreSQL (Docker, production)
        +--> optional local Sentence Transformers model
        +--> optional OpenAI API (explicit consent only)
```

## Backend modules

| Module | Responsibility |
| --- | --- |
| `main.py` | App factory, lifespan, CORS, logging, rate limiting, error handlers, routers. |
| `config.py` | Environment-backed settings (single source of truth). |
| `database.py` | Engine, session factory, declarative base, FastAPI dependency. |
| `models/db.py` | ORM entities and JSON columns for computed artefacts. |
| `models/schemas.py` | Typed API contracts. Legacy fields retained. |
| `security.py` | bcrypt password hashing, JWT access/refresh tokens, current-user dependency. |
| `services/skill_taxonomy.py` | Canonical skills, aliases, categories, related/transferable skills. |
| `services/analyzer.py` | Extraction, hybrid matching, evidence classification, suggestions, resume updates. |
| `services/resume_parser.py` | Safe upload validation and PDF/DOCX text extraction. |
| `services/resume_structurer.py` | Section detection and structured resume JSON with confidence/warnings. |
| `services/job_service.py` | Job title/company/experience/education extraction and required-vs-preferred skill classification. |
| `services/ats_service.py` | Explainable alignment score with component breakdown. |
| `services/rewrite_service.py` | Conservative rule-based rewriting; optional consented LLM draft. |
| `services/learning_path_service.py` | Stage-based plans prioritized by requirement level. |
| `services/interview_service.py` | Question generation and heuristic mock-answer feedback. |
| `services/job_match_service.py` | Multi-job ranking with transparent weights. |
| `routes/analyzer.py` | Existing analysis endpoints + combined `/analyze`. |
| `routes/auth.py` | Registration, login, refresh, logout, profile, account deletion. |
| `routes/history.py` | Saved resumes, jobs, analyses, interview sessions. |

## Data model

- `users` — identity and profile.
- `refresh_tokens` — hashed, revocable refresh tokens.
- `resumes` — extracted text, structured JSON, confidence, warnings (owned by user).
- `job_descriptions` — raw text and structured intelligence (owned by user when saved).
- `analyses` — comparison, ATS, suggestions and learning-plan JSON snapshots.
- `interview_sessions` / `interview_answers` — generated questions, answers and heuristic feedback.

All user-owned queries filter by `user_id`; ownership checks return 404 to avoid resource enumeration.

## API compatibility

Legacy endpoints and aliases remain. New fields are additive. The only intentional semantic
changes are:

1. Skill names are more specific (e.g. `postgresql` instead of collapsing to `sql`).
2. Semantic similarity is reported as a *related/partial* match, not as proven experience.
3. LLM rewriting requires per-request consent even when a key is configured.

Both changes are documented in `docs/TECHNICAL_DECISIONS.md`.

## Frontend structure

- `App.jsx` — providers + router.
- `context/AuthContext.jsx` — token lifecycle and current user.
- `components/layout/AppLayout.jsx` — navigation, account menu, footer.
- `components/ui/*` — buttons, cards, toasts, empty/loading states, score ring.
- `pages/*` — landing, auth, dashboard, analyze, results, jobs, history, interview, profile.
- `components/results/*` — skills, evidence, ATS, rewrite, learning, interview panels.
- `services/api.js` — all HTTP concerns, auth header injection, refresh retry.
