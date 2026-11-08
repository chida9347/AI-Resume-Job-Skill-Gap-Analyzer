# Roleprint project audit

## Scope and architecture

The existing project is a small FastAPI service (`backend/`) and React/Vite single-page application (`frontend/`). The browser uploads a resume, asks the API to extract resume text and recognized skills, analyzes job text, compares skills, and requests ATS feedback, rewriting, learning paths, and interview prompts. Uploaded content and analysis history are not persisted. The optional OpenAI rewriter requires an explicit environment opt-in; the default uses local deterministic logic.

## Existing functionality and implementation status

| Area | Existing implementation | Audit finding |
|---|---|---|
| UI | Landing, upload/job input, results, resume editor, interview prep, responsive styling | A consistent multi-step product flow already exists; no separate profile/settings, saved history, or account system. |
| Resume upload | PDF via pypdf; DOCX via python-docx; 10 MB cap; empty/unsupported/unreadable errors | Text-only extraction; scanned PDFs need OCR. DOCX tables were omitted (now included). Confidence was not surfaced (now a heuristic is returned and shown). |
| Skill recognition | Explicit phrase taxonomy, optional spaCy matcher, optional local embeddings | Maintainable and deterministic baseline, but taxonomy coverage is finite. No section-level resume extraction or reliable education/employment entity extraction. |
| Job analysis | Same phrase taxonomy applied to all text | Previously labeled every result required and did not distinguish preferred skills (now explicit preferred sections are separated). Responsibilities and education are not structurally parsed. |
| Skill comparison | Canonical skill list match, optional semantic helper | Useful wording comparison, not a qualification judgment. Preferred skills now appear separately. Partial proficiency and evidence-level matching remain unsupported. |
| ATS estimate | Keyword, section, and formatting heuristics | Generic frequent words could dominate keywords (now restricted to known skills). Current score breakdown is explainable, but relevance and experience/project/education alignment are only approximate. |
| Resume rewrite and edit chat | Rule-based edits to experience bullets; side-by-side UI; editor chat with local literal edits and optional OpenAI instructions | Preserves the current draft, reports each applied change, and retains the existing PDF download action. General AI edits require the existing explicit OpenAI opt-in; factual accuracy still needs user review. |
| Learning plan | Deterministic plans for selected skills and a generic fallback | Actionable basics with exercises/project/duration; not staged by beginner/intermediate/advanced and no external course catalog. |
| Interview prep | Deterministic general role prompts and frameworks | No resume-project or missing-skill context, answer entry, or interactive feedback loop. |
| Backend reliability | FastAPI routes and Pydantic validation; CORS limited to localhost | Core errors return HTTP errors; no authentication, request rate limiting, structured logs, persistence, or production deployment configuration. Upload signature checks and DOCX table extraction were added. |
| Tests/docs | Unit tests for core services and a short README | Existing service tests cover basic behavior; API integration, actual uploaded-file fixtures, browser responsiveness, and deployed startup are not covered. README documents local setup and API routes. |

## Changes made in this upgrade

- Classify skills from clearly marked preferred sections separately from required skills, including mixed required/preferred labels on one line, while returning soft/technical groupings.
- Carry preferred skills through the existing compare API and results UI.
- Include DOCX table text and reject files whose PDF/DOCX signatures do not match their extension.
- Return a cautious extraction-confidence indicator, detected common sections, and word count; surface low/medium confidence in results.
- Restrict ATS keyword matching to the explicit skill taxonomy and show weighted score contributions for keywords, required/preferred coverage, section completeness, and readability.
- Add service tests for preferred-skill classification/comparison and ATS breakdown arithmetic.
- Add a resume-edit chat API and editor panel. Local mode supports quoted replacement/removal and adding user-supplied text to a section; broader instructions use the optional configured OpenAI service or return a clear no-change response.
- Add regression tests for local resume-chat edits and unsupported requests.

## Remaining work

The larger requested roadmap is not fully implemented: robust section/entity extraction, partial skill evidence, richer gap-specific teaching plans, role/resume-derived interview questions and mock practice, persistence/accounts, production hardening, and full end-to-end/browser validation remain future work. These would require broader contracts and product decisions than a targeted reliability upgrade. No account or database was introduced because this app currently promises in-memory processing and has no history feature.

## Verification

The backend service suite passes (20 tests), Python compilation succeeds, and `git diff --check` is clean. The edit endpoint was smoke-tested directly and the editor chat was verified end to end with a synthetic resume, including updating the displayed text and retaining the download action. The app remains running locally. Vite could not start its scanner/transformer because the environment blocks child-process spawning (`EPERM`), so the frontend source was bundled directly with the installed esbuild executable and served locally. API dependencies were loaded from PyPI wheels in the task work directory because pip's normal unpack step was denied. These run accommodations do not alter project dependency lockfiles. The requested Git commit could not be created because the managed profile denied writes to `.git/index.lock`.
