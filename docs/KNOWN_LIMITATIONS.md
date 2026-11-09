# Known Limitations

Roleprint is deliberately honest about what it can and cannot do. This page
lists current limits so they are not mistaken for bugs or guarantees.

## Matching and scoring

- **Matching is lexical-first.** The default path uses a curated taxonomy,
  aliases and text evidence. It understands common synonyms but not arbitrary
  paraphrase, context or seniority.
- **Semantic matching is optional and partial.** It requires a locally cached
  sentence-transformers model and never downloads one implicitly. Semantic-only
  matches are labelled `partial` and never count as proven experience.
- **The taxonomy is finite.** About 205 skills are curated. Niche, internal or
  newly coined tools may be missed. Unknown terms are not guessed.
- **Evidence classification is heuristic.** `strong`, `mentioned`, `implied`,
  `partial` and `missing` are text-derived labels, not a human assessment.
- **ATS scores are estimates.** They follow a documented checklist (keyword
  relevance, required/preferred coverage, sections, readability) with caps. They
  are not any employer's proprietary ATS result and must not be presented as
  one. The UI intentionally avoids misleading 95–100 scores when evidence is
  missing.
- **Confidence reflects extraction and coverage**, not the probability of
  getting an interview or an offer.
- **Evaluation is a sanity check.** The dataset is small and hand-labelled.
  Reported precision/recall/F1 describe that dataset only, not general accuracy.

## Parsing and documents

- **English-oriented.** Section detection, skill aliases and question templates
  are built for English-language resumes and postings.
- **PDF/DOCX only for upload.** Plain text is supported by paste. Other formats
  are rejected with a clear error.
- **Layout is not reconstructed.** Text order is extracted; columns, tables,
  graphics and styling may be lost or reordered. DOCX table text is included but
  not positioned.
- **Scanned PDFs need OCR.** OCR is off by default and requires extra packages
  plus the Tesseract binary. Without it, image-only PDFs fail rather than
  producing empty text.
- **Uploads are bounded** by size, page count and text length. Larger documents
  are rejected.
- **PDF export reformats reviewed text.** It does not reproduce the original
  document's layout, fonts or pagination. "Fit to one page" stops rather than
  shrinking text below legibility.

## Content generation

- **No invented facts.** Rewrites and suggestions preserve source facts and use
  explicit placeholders such as `[add measurable result]` instead of inventing
  metrics, employers, dates, certifications or skills.
- **Rule-based rewriting is conservative.** It reorders and reframes existing
  content; it does not perform deep creative rewriting unless OpenAI is enabled.
- **OpenAI output is not verified.** When enabled, generated text can still be
  inaccurate or generic. The UI requires review and the user is responsible for
  every line. Each request needs consent unless configured otherwise.
- **Learning paths are suggestions**, not endorsements of courses or guarantees
  of employability. They are rule-based and not personalised to local job
  markets.

## Accounts, data and privacy

- **Tokens are stored in `localStorage`.** This is simple and survives reloads
  but is exposed to XSS. A hardened deployment should consider httpOnly cookies
  with CSRF protection.
- **No email verification or password reset.** Accounts use email + password
  only. There is no email delivery, MFA or social login.
- **No roles or administration UI.** There is no admin console, audit trail or
  team/workspace sharing.
- **Saved analyses are read-only snapshots.** They store computed results, not
  the resume text or rewrite draft. Editing requires re-running an analysis.
- **Anonymous analysis is not persisted.** History requires an account.
- **Account deletion is immediate and irreversible.** Backups may retain copies
  until their own retention period expires.
- **No encryption at rest by the application.** Rely on database/volume
  encryption and access controls at the infrastructure layer.
- **No background processing.** Long optional AI calls run inside the request.

## Operations and scale

- **Rate limiting is in-memory per process.** Multiple workers or replicas each
  enforce their own limits. Use a shared store (for example Redis) before
  horizontal scaling if global limits matter.
- **Single-region, single-database design.** There is no sharding, read replica
  routing or multi-region failover built in.
- **No built-in observability stack.** Logs are structured JSON to stdout with
  request IDs; metrics and tracing must be added by the operator.
- **No background job queue or scheduler.** All work is request-scoped.
- **No live job-board integration.** Jobs are pasted manually; integrations would
  require third-party credentials and terms.
- **No browser-level end-to-end suite.** Component and API tests exist; a
  Playwright journey is documented as optional and is not part of CI.
- **No real cloud deployment was performed.** Docker and deployment instructions
  are provided and locally verified, not operated in a public cloud.

## Repository and branding

- **`CNAME` contains a placeholder domain** (`www.resume.analyzer.com`). Replace
  it with a real domain before enabling GitHub Pages, or remove it if unused.
- **No license file is included.** Add one before distributing the project.
- **Bundle size warning.** The production frontend build emits a chunk-size
  warning from charting and PDF libraries. It is functional; route-level code
  splitting is a future optimisation.

## Accessibility and UX

- **Automated accessibility checks are not part of CI.** Components use labels,
  roles and focus styles, but a full WCAG audit has not been performed.
- **Mobile layouts are responsive but not separately designed.** Complex tables
  and charts may be dense on small screens.
