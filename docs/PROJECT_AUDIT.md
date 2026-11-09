# Roleprint — Project Audit (baseline)

Audit date: 2026-11-08. Audited commit: `14535d3` (plus the existing untracked `desktop.ini`).
The audit was produced by reading every source file and by running the existing build/test tooling.
No feature was assumed to work because code existed.

## 1. What exists

| Layer | Implementation |
| --- | --- |
| Backend | FastAPI application in `backend/main.py`, one router (`routes/analyzer.py`), Pydantic schemas, five service modules. |
| Resume ingestion | `POST /upload_resume` accepts PDF (`pypdf`) and DOCX (`python-docx`) up to 10 MB, extracts plain text, returns skills. |
| Skill extraction | Deterministic alias dictionary of 38 skills in `services/analyzer.py`; optional spaCy `PhraseMatcher`; optional local Sentence Transformers similarity. |
| Job analysis | `POST /analyze_job` returns one flat list of skills. |
| Comparison | `POST /compare` exact match plus optional semantic match; returns matched/missing lists and a percentage. |
| ATS | `POST /ats-score` weighted keyword overlap (60%), 3-section completeness (25%), formatting heuristics (15%). |
| Resume rewriting | Rule-based experience-bullet rewrite with metric placeholders; optional OpenAI rewrite behind env flags. |
| Suggestions | Missing-skill confirmation prompts plus one length-based note. |
| Learning paths | Six hard-coded plans plus a generic fallback; 4 steps, one project, one duration. |
| Interview | `GET /interview_tips` returns three static questions, independent of the resume or job. |
| Persistence | None. No database, no accounts, no history. |
| Frontend | React 19 + Vite 6 single-page state machine (`App.jsx`, 430 lines), 9 components, one large hand-written CSS file. |
| Tests | 13 `unittest` cases covering the services only. |
| Docs | Short README, no architecture or API documentation. |

## 2. Verified working

- `npm run build` succeeds (verified 2026-11-08, Vite 6.4.3).
- Backend dependencies install on Python 3.14 (FastAPI 0.162, spaCy 3.8.18).
- PDF/DOCX text extraction path is real; corrupt/empty files return HTTP 400 and oversized files HTTP 413.
- Existing service tests are meaningful and assert behaviour, not mocks.
- Rule-based rewriting genuinely avoids inventing metrics (adds explicit placeholders).
- PDF export is real (`jsPDF`), and it intentionally exports extracted text rather than preserving layout.
- The UI has a coherent visual identity, responsive breakpoints, loading/error states, and accessible focus styles.

## 3. Broken or incorrect

1. **Confirmed-skills review banner bug** (`App.jsx:407`): compares suggestion *ids* with accepted *skill names*, so the "other selections added as review notes" banner appears incorrectly.
2. **spaCy matcher length guard is meaningless**: `nlp.blank("en").max_length` is ~1,000,000, so the fallback is almost never used for realistic input.
3. **`/analyze_job` is not job intelligence**: it returns every skill as "required"; preferred/must-have wording is ignored.
4. **ATS keyword extraction counts arbitrary nouns** as job keywords, diluting keyword match and producing feedback such as "Missing important keyword: solutions".
5. **ATS section model is incomplete**: projects, certifications and contact details are not evaluated; there is no explanation of awarded points.
6. **Interview content ignores the resume and the job** entirely; the same three questions are returned for every role.
7. **Frontend analysis is four sequential requests** (`upload` → `analyze_job` → `compare` → `suggestions`). A failure in the last request discards a valid analysis.
8. **`CompareInput` lists are unbounded**; there is no per-list length limit or deduplication.
9. **`extract_skills` conflates distinct technologies**: PostgreSQL/MySQL/SQLite collapse to `sql`, GitHub/GitLab collapse to `git`, Tailwind/Sass collapse to `css`. This makes gap explanations misleading.
10. **No evidence extraction**: a skill in a "Skills" list and a skill used in a quantified project are treated identically.
11. **Rewrite exception handling is silent** (`except Exception: return None`), hiding provider/configuration failures.
12. **DOCX tables are ignored**, and PDF extraction has no page limit or magic-byte validation.
13. **No logging, request IDs, rate limiting, or centralized error handling.**
14. **CORS origins are hard-coded.**
15. **No `.env.example`**, despite optional OpenAI and NLP configuration.
16. **UI type scale is too small**: many labels are 8–10 px, below comfortable readability.
17. **`CNAME` contains the placeholder `www.resume.analyzer.com`**, which is not a valid deployment target for this app.
18. **Frontend has no routing, history, dashboard, account, or settings**, so results cannot be revisited.

## 4. Missing relative to the target product

- Structured resume extraction (contact, education, experience, projects, certifications, confidence/warnings).
- OCR for scanned PDFs (optional pipeline).
- Required vs preferred skill separation with evidence and explanations.
- Partial/transferable skill classification.
- Multi-job comparison and ranking.
- Explainable ATS breakdown with component weights and required/preferred coverage.
- Actionable, editable resume improvement suggestions with accept/reject.
- Stage-based learning roadmap with objectives, concepts, exercises and priority.
- Role- and resume-specific interview questions plus mock-answer feedback.
- Accounts, authentication, persistence, history, saved resumes/jobs, data deletion.
- Security hardening (validation, rate limiting, structured logging, secret handling).
- Docker, CI, API docs, evaluation dataset, and a real testing strategy.

## 5. Technical debt

- Business logic lives partly in route handlers; response shapes are untyped dicts for most endpoints.
- One 430-line `App.jsx` owns fetching, state, PDF rendering and page composition.
- `styles.css` contains a first design pass followed by a second override pass (duplicated rules, two responsive systems).
- The skill dictionary, ATS stopwords and rewrite action verbs duplicate concepts.
- No shared error/response contract; each component formats errors itself.
- No migration path or schema ownership.

## 6. Risks to preserve

- Existing route names and aliases (`/ats_score`, `/rewrite_resume`, `/learning_path`) are used by the frontend and must remain.
- Existing response keys (`matched_skills`, `missing_skills`, `similarity_score`, `ats_score`, `section_score`, `suggestions`, `paths`, `updated_resume_text`) must remain valid.
- The app must work without an OpenAI key and without downloading models.
- Uploaded resume content must not be persisted by default in the no-account flow.

## 7. Recommended architecture (implemented in this upgrade)

- Keep the modular monolith: FastAPI + service layer + SQLAlchemy 2.0 persistence.
- SQLite by default for zero-config local development; PostgreSQL in Docker/production via `DATABASE_URL`.
- Alembic migrations; optional `AUTO_CREATE_TABLES` for local first run.
- Optional features (OpenAI, Sentence Transformers, OCR) stay opt-in and degrade gracefully.
- New persistence/auth endpoints are additive; analysis endpoints remain usable anonymously.
- Frontend moves to React Router with a shared layout, auth context, and reusable result components.
