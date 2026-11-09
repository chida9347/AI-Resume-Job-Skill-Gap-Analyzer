# Implementation Roadmap

Status legend: `[x]` implemented and verified, `[~]` implemented but partially verified, `[ ]` not implemented.

## Phase 1 — Foundation, parsing, matching, evaluation
- [x] Audit existing behaviour and preserve API aliases.
- [x] Central configuration, structured logging, request IDs, rate limiting, error contract.
- [x] Safe upload validation (extension + magic bytes + size + page/text limits).
- [x] Structured resume extraction with confidence and warnings (contact, education, experience, projects, certifications, skills).
- [x] Optional OCR hook (opt-in, clear error when unavailable).
- [x] Canonical skill taxonomy with aliases, categories, related skills.
- [x] Hybrid matching: exact, synonym, semantic (optional), evidence, partial/transferable.
- [x] Evidence snippets with section and strength classification.
- [x] Unit tests for parsing, matching, false positives and API contracts.
- [x] Versioned evaluation dataset and metrics script (precision/recall/F1, false positives).

## Phase 2 — Job intelligence, multi-job matching, ATS, suggestions
- [x] Required vs preferred vs mentioned skill classification.
- [x] Job title, company, experience, education, responsibilities, keywords.
- [x] Explainable ATS breakdown with weights, coverage and confidence.
- [x] Multi-job comparison and transparent ranking.
- [x] Evidence-aware resume suggestions with accept/reject workflow.

## Phase 3 — Learning, interview, frontend
- [x] Stage-based learning roadmaps with priority, objectives, concepts, exercises, projects.
- [x] Role/resume/missing-skill interview question generation.
- [x] Mock interview with heuristic answer feedback and stored attempts.
- [x] React Router, shared layout, dashboard, history, profile/settings.
- [x] Results UI with charts, progress indicators, empty/loading/error states.

## Phase 4 — Persistence and accounts
- [x] SQLAlchemy models, SQLite local default, PostgreSQL via `DATABASE_URL`.
- [x] Alembic initial migration.
- [x] Registration, login, refresh-token rotation, logout, profile, account deletion.
- [x] User isolation tests.
- [x] Saved resumes, jobs, analyses and interview sessions.

## Phase 5 — Production readiness
- [~] Backend/frontend Dockerfiles, Docker Compose with PostgreSQL. Authored but not executed locally because Docker is not installed in the build environment.
- [~] GitHub Actions CI (backend tests, frontend tests and build). Workflow authored but not yet run on GitHub.
- [x] `.env.example`, deployment notes, known limitations.
- [x] CORS and secrets from environment.
- [x] Rate limiting and privacy-conscious logging.

## Phase 6 — Verification
- [x] Backend test suite passing (120 tests).
- [x] Frontend production build passing.
- [x] Frontend component tests passing (25 tests).
- [x] Live API smoke test: health, analyze, ATS and aliases, learning paths and aliases, interview questions/evaluation, multi-job ranking, rewrite, register, profile, save/list/detail/export/delete history, logout.
- [ ] Browser-level Playwright journey (documented as optional; not required to run the app).
- [ ] Real cloud deployment (not performed; deployment instructions provided).
- [ ] Docker Compose startup verification (blocked locally: Docker is unavailable).

## Verification notes

Verified on 2026-11-10 on Windows with SQLite:

- `backend`: `pytest -q` → 120 passed, 1 third-party deprecation warning.
- `frontend`: `npm run test:run` → 6 files, 25 tests passed.
- `frontend`: `npm run build` → success (chunk-size warning only).
- Live API on `127.0.0.1:8123` with a temporary SQLite database: all smoke
  endpoints returned 2xx. The ATS result was 60 with one active cap, confirming
  the estimate is not artificially inflated. Rewriting reported `rule-based`
  because no OpenAI consent was supplied.

Docker and CI were not executed in this environment. Treat their status as
"implemented, unverified" until a machine with Docker and a GitHub runner
confirms them.

## Deliberate non-goals
- Live job-board integrations (would require third-party credentials and terms).
- Claiming an employer ATS score; the product reports an estimated alignment score.
- Automatic resume fact invention; placeholders are explicit and user-editable.
