# Roleprint — AI Resume Intelligence Platform

Roleprint compares a resume with one or more job descriptions and explains the
result: which skills are evidenced, which are only mentioned or implied, which
are missing, how the resume scores against an **estimated** ATS checklist, what
to learn next, and how to prepare for an interview.

The application is a FastAPI service and a React/Vite single-page app. It works
fully offline with SQLite and deterministic matching. OpenAI rewriting and local
sentence-transformer similarity are optional and disabled by default.

> **Honesty contract.** Semantic similarity is never presented as proven
> experience. Scores are labelled estimates and are capped when evidence is
> missing. The product never invents employment history, metrics, skills or
> certifications; anything generated is an explicit, editable placeholder.

---

## What it does

| Area | Behaviour |
| --- | --- |
| Resume parsing | PDF/DOCX upload with magic-byte, size, page and text checks; plain-text paste; structured extraction of contact, education, experience, projects, certifications and skills with confidence and warnings. |
| Skill matching | Hand-curated taxonomy (~205 skills) with aliases, categories and related skills. Exact, synonym, evidence and optional semantic matching. Evidence statuses: `strong`, `mentioned`, `implied`, `partial`, `missing`. Semantic-only matches are `partial`. |
| Job intelligence | Separates required, preferred, mentioned and soft skills. Extracts title, company, experience, education and responsibilities. |
| ATS estimate | Explainable breakdown with weights, point contributions, score caps and confidence. Never reports a misleading 95–100. |
| Multi-job ranking | Compare one resume against up to 25 postings with transparent, configurable component weights. |
| Learning roadmap | Stage-based plans for missing and partial skills, with objectives, concepts, exercises and project ideas. |
| Interview prep | Role- and resume-grounded questions, answer frameworks, expected concepts and heuristic answer feedback. |
| Editing | Review-first suggestions, rule-based rewrite draft, chat-style edits with explicit quoted replacements, and PDF export of reviewed text. |
| Accounts | Registration, login, refresh-token rotation, logout, profile, password change, data export, history clearing and account deletion. |
| History | Saved resumes, jobs, analyses and interview sessions, isolated per user. Analyses are read-only snapshots. |

The visual identity (paper tones, deep green, leaf accent, serif display type)
is preserved from the original Roleprint design.

---

## Tech stack

- **Backend:** Python 3.10+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic,
  PyJWT, bcrypt, pypdf, python-docx, spaCy.
- **Database:** SQLite by default; PostgreSQL 16 via `DATABASE_URL`.
- **Frontend:** React 19, Vite 6, React Router 7, Recharts, Axios, Lucide icons,
  Tailwind directives plus a hand-written stylesheet.
- **Tests:** pytest + httpx for the API; Vitest + Testing Library for the UI.
- **Packaging:** Docker multi-stage builds, Docker Compose, nginx SPA proxy,
  GitHub Actions CI.

---

## Repository layout

```text
backend/
  main.py            FastAPI app factory, middleware, health
  config.py          environment-backed settings
  database.py        engine, session, base
  models/            Pydantic contracts and SQLAlchemy entities
  routes/            analyzer, auth, history routers
  services/          taxonomy, parsing, matching, ATS, jobs, learning,
                     interviews, rewriting, uploads
  alembic/           migration environment and initial revision
  evaluation/        hand-labelled dataset and metrics script
  tests/             pytest suite
frontend/
  src/pages/         landing, auth, analyze, results, editor, roadmap,
                     interview, jobs, history, saved analysis, profile,
                     settings, 404
  src/components/    reusable UI, results panels, charts, layout
  src/context/       auth and workspace state
  src/services/      auth-aware API client and token store
  src/utils/         analysis normalisation, formatting, errors, PDF export
docs/                audit, architecture, decisions, roadmap, deployment,
                     known limitations
```

---

## Quick start (local)

Requirements: Python 3.10+ and Node.js 18+.

### 1. Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item ..\.env.example .env   # edit JWT_SECRET and other values
uvicorn main:app --reload --port 8000
```

The API creates local tables on startup when `AUTO_CREATE_TABLES=true` (the
development default). Health check: <http://localhost:8000/health>. Interactive
docs: <http://localhost:8000/docs>.

### 2. Frontend

```powershell
cd frontend
npm install
# create frontend/.env.local with: VITE_API_URL=http://localhost:8000
npm run dev
```

Open the Vite URL (normally <http://localhost:5173>). Analysis works without an
account. Sign in to save analyses and use history, profile and settings.

### 3. Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest

cd ..\frontend
npm run test:run
npm run build
```

---

## Environment configuration

All backend settings come from environment variables or `backend/.env`. The
full template is [`.env.example`](.env.example). The most important values:

| Variable | Default | Notes |
| --- | --- | --- |
| `ENVIRONMENT` | `development` | Use `production` when deployed. |
| `DATABASE_URL` | `sqlite:///./roleprint.db` | Use `postgresql+psycopg://user:pass@host:5432/db` in production. |
| `AUTO_CREATE_TABLES` | `true` | Set `false` in production and run Alembic. |
| `JWT_SECRET` | development placeholder | **Must** be replaced before deployment. |
| `CORS_ORIGINS` | local Vite origins | Comma-separated explicit origins. |
| `ENABLE_RATE_LIMIT` | `true` | In-memory limiter per client IP. |
| `ENABLE_SEMANTIC_MATCHING` | `true` | Uses a local model only if one is installed. |
| `ENABLE_OPENAI_REWRITER` | `false` | Requires `OPENAI_API_KEY` and per-request consent. |
| `ENABLE_OCR` | `false` | Requires pytesseract and the Tesseract binary. |

Frontend builds read `VITE_API_URL` at build time. Use `http://localhost:8000`
for local development and `/api` behind the Docker nginx proxy.

---

## Docker Compose

The Compose stack runs PostgreSQL 16, the API (migrations first, then uvicorn)
and an nginx-served frontend.

```powershell
Copy-Item .env.example .env
# Edit .env: set a strong JWT_SECRET and POSTGRES_PASSWORD.
docker compose up --build
```

Open <http://localhost:8080>. The nginx container proxies `/api/` to the backend
and serves the SPA with history fallback.

The API is also exposed on <http://localhost:8000> for direct calls and health
checks. Set `CORS_ORIGINS` if you call it directly from another origin.

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for reverse-proxy, TLS, database
backup, scaling and operational guidance.

---

## Database and migrations

SQLite is the zero-configuration default. PostgreSQL is selected with
`DATABASE_URL`. Alembic is the schema source of truth for production:

```powershell
cd backend
alembic upgrade head          # apply migrations
alembic revision --autogenerate -m "describe change"
alembic downgrade -1          # roll back one revision
```

The initial revision creates users, refresh tokens, resumes, jobs, analyses and
interview sessions. Compose runs `alembic upgrade head` automatically.

---

## API overview

Public analysis endpoints (no account required):

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Liveness and enabled feature flags. |
| `POST` | `/upload_resume` | Multipart PDF/DOCX upload and text extraction. |
| `POST` | `/parse-resume` | Structured extraction from pasted resume text. |
| `POST` | `/analyze_job` | Job intelligence: required/preferred/soft skills. |
| `POST` | `/compare` | Skill comparison with evidence and status. |
| `POST` | `/analyze` | Primary combined analysis used by the frontend. |
| `POST` | `/ats-score` | Explainable ATS estimate. |
| `POST` | `/job-match` | Rank up to 25 jobs against one resume. |
| `POST` | `/rewrite-resume` | Rule-based or consented AI rewrite draft. |
| `POST` | `/edit-resume` | Chat-style instruction-based edit. |
| `POST` | `/suggestions` | Evidence-aware suggestions. |
| `POST` | `/update_resume` | Apply confirmed suggestions to text. |
| `POST` | `/learning-path` | Stage-based learning plans. |
| `GET` | `/interview_tips` | Role-based questions and tips. |
| `POST` | `/interview/questions` | Grounded question generation. |
| `POST` | `/interview/evaluate` | Heuristic answer feedback. |

Authentication and persistence (Bearer token required):

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout` | Token lifecycle. |
| `GET`/`PATCH`/`DELETE` | `/auth/me` | Profile and account deletion. |
| `POST` | `/auth/change-password` | Password change. |
| `GET`/`POST`/`DELETE` | `/resumes`, `/jobs`, `/analyses`, `/interviews` | Saved history. |
| `GET` | `/history/export` | Download all saved data as JSON. |
| `DELETE` | `/history` | Clear saved history. |

Compatibility aliases `/ats_score`, `/rewrite_resume` and `/learning_path`
remain available and are hidden from the OpenAPI schema.

### Combined `/analyze` response

`structured_resume`, `resume_skills`, `job`, `comparison`, `ats`, `suggestions`,
`learning_paths`, `interview`, `meta`.

### Authentication

Access tokens are short-lived; refresh tokens rotate on use. The frontend stores
tokens in `localStorage` and refreshes automatically once on a 401. Logging out
revokes the stored refresh token. All saved resources are scoped by `user_id`;
cross-user access returns `404`.

---

## Privacy and data handling

- Anonymous analysis does not persist resume text.
- Resume text is processed in memory. Saved resumes store text only when the
  user explicitly saves them while signed in.
- Saved analyses are snapshots of computed results; they do not include the
  resume text or rewrite draft.
- Raw resume text and PII are never written to application logs. Errors carry a
  request ID for correlation.
- Users can export and delete their data from Settings.

---

## Optional AI features

**OpenAI rewriting** is off unless `ENABLE_OPENAI_REWRITER=true` and
`OPENAI_API_KEY` are set. Even then, each request must opt in unless
`OPENAI_CONSENT_DEFAULT=true`. Enabling it sends the resume text and job
description to OpenAI. Install `backend/requirements-openai.txt`.

**Semantic matching** uses a local sentence-transformers model when one is
cached. Install `backend/requirements-nlp.txt`; the app never downloads a model
implicitly and falls back to lexical matching when unavailable.

**OCR** requires `ENABLE_OCR=true`, `backend/requirements-optional.txt` and the
Tesseract binary. Scanned PDFs fail with a clear message otherwise.

---

## Evaluation

`backend/evaluation/dataset.json` contains hand-labelled cases. The script
isolates matching quality by querying with the labelled required skills:

```powershell
cd backend
.\.venv\Scripts\python.exe -m evaluation.evaluate
```

Reported on the current dataset: required-skill extraction P/R/F1 = 1.000;
matching keyword F1 = 0.750, synonym F1 = 0.833, hybrid F1 = 1.000; false
positive rate = 0.000 for all three methods; hybrid precision@3 = 1.000.

These numbers come from a small, hand-labelled sanity set, not a benchmark.
Do not present them as general accuracy claims.

---

## Documentation

- [`docs/PROJECT_AUDIT.md`](docs/PROJECT_AUDIT.md) — baseline audit.
- [`docs/CURRENT_ARCHITECTURE.md`](docs/CURRENT_ARCHITECTURE.md) — module map and data flow.
- [`docs/TECHNICAL_DECISIONS.md`](docs/TECHNICAL_DECISIONS.md) — trade-offs and rationale.
- [`docs/IMPLEMENTATION_ROADMAP.md`](docs/IMPLEMENTATION_ROADMAP.md) — delivered scope and non-goals.
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — production deployment guide.
- [`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md) — honest limits.

---

## Compatibility

The original public routes, response keys and underscore aliases are preserved.
The project remains a modular monolith: services are separated by responsibility,
not by network boundary. No user data or resume content is committed to the
repository.
