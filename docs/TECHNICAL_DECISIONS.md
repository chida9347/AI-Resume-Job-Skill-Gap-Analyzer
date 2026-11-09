# Technical Decisions

## 1. Modular monolith, not microservices
The product is a single-user workflow with CPU-bound text processing. A monolith keeps
deployment and local setup simple. Services are separated by responsibility, not by network.

## 2. SQLite locally, PostgreSQL in production
`DATABASE_URL` selects the database. SQLite gives a zero-configuration local experience and
keeps the original "clone and run" promise. Docker Compose and the deployment guide use
PostgreSQL. SQLAlchemy 2.0 and Alembic work with both. JSON columns are used for computed
artefacts (comparison, ATS, suggestions) because they are snapshots, not relational entities.

## 3. Anonymous analysis remains available
The original product required no account. Requiring login for the core flow would be a
regression. Analysis endpoints stay public; saving, history and mock-interview tracking
require authentication. This also avoids storing resumes for anonymous users.

## 4. Skill taxonomy is explicit and version-controlled
A hand-curated taxonomy is auditable, testable, and works offline. Aliases are matched with
word boundaries to avoid `java` matching `javascript`. Distinct products (PostgreSQL, MySQL,
SQLite) are separate canonical skills. Related skills are used for *partial* matches, never
for exact matches.

## 5. Semantic similarity is a signal, not proof
Sentence Transformers are optional and loaded locally only (no implicit downloads). A high
cosine similarity marks a skill as `related`/partial. It does not count as demonstrated
experience. This prevents the common failure where "machine learning" is treated as proof
that a candidate knows "deep learning".

## 6. Evidence matters more than keyword presence
Every detected resume skill is located in a section and sentence. A skill used in an
experience/project sentence with an action verb or metric is `strong`; a bare list entry is
`mentioned`. The UI and ATS show this distinction.

## 7. ATS score is explainable and bounded
The score is an estimated resume-to-job alignment score. It is a weighted sum of required
coverage, preferred coverage, section completeness, formatting, experience alignment,
education relevance and project relevance. Every component reports its weight, raw score,
awarded points and a human-readable explanation. The response carries an explicit
disclaimer. Scores are capped at 97 unless every required skill is strongly evidenced;
even then the UI calls it an estimate.

## 8. Rewriting never invents facts
The rule-based rewriter only changes wording, formatting and placeholders. It cannot add
employers, dates, metrics, skills or certifications. Missing metrics become the literal
placeholder `[add a verified outcome metric]`. The LLM path is opt-in per request, and the
system prompt forbids fabrication. The UI requires the user to review before applying.

## 9. OpenAI and OCR are optional
No key and no model download are required. If optional packages or credentials are absent,
the deterministic path is used. Failures are logged (without resume content) and surfaced
as a rule-based fallback, not silently swallowed.

## 10. Refresh tokens are stored hashed and rotated
Access tokens are short-lived JWTs. Refresh tokens are random opaque strings stored as
SHA-256 hashes with expiry and revocation. Rotation on refresh limits replay. Logout revokes
the presented token. Passwords use bcrypt with a per-password salt.

## 11. User isolation is enforced in queries
Every persisted resource is queried with `user_id = current_user.id`. Missing resources and
other users' resources both return 404, preventing enumeration.

## 12. Frontend: React Router + small state layer
The original single-component state machine made history and deep links impossible. Routing
adds real pages without changing the visual identity. Server state is fetched through one
API module; auth state lives in a context. Charts use Recharts; no fake data is rendered.

## 13. Intentional API changes
- Skill canonical names are more specific (`postgresql`, `mysql`, `github`, `tailwind`).
- Semantic similarity is reported under `partial_skills`, not `matched_skills`.
- `section_score` gains projects/certifications/contact keys.
- LLM rewriting requires `ai_consent: true` (or `OPENAI_CONSENT_DEFAULT=true` for a trusted
  single-user deployment).
All legacy routes, aliases and response keys remain.
