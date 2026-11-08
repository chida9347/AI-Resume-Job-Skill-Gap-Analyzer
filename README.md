# AI Resume & Job Skill Gap Analyzer

Roleprint compares a resume with a job description, surfaces explicit skill matches and gaps, and offers editable interview and resume-review prompts.

## Run locally

Requirements: Python 3.10+ and Node.js 18+.

Start the API in one terminal:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

Start the frontend in a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL (normally `http://localhost:5173`). Set `VITE_API_URL` in `frontend/.env.local` to use an API at a different origin. FastAPI's local CORS allowlist should also be updated for the deployed frontend origin before deployment.

## API

- `GET /health`
- `POST /upload_resume` (multipart PDF/DOCX, up to 10 MB)
- `POST /analyze_job` (`{"text":"..."}`)
- `POST /compare` (`{"resume_skills":[...],"job_skills":[...]}`)
- `POST /ats-score` (`{"resume_text":"...","job_description":"..."}`)
- `POST /rewrite-resume` (`{"resume_text":"...","job_description":"..."}`)
- `POST /edit-resume` (`{"resume_text":"...","instruction":"..."}`)
- `POST /learning-path` (`{"missing_skills":[...]}`)
- `POST /suggestions` (`{"missing_skills":[...],"resume_text":"..."}`)
- `POST /update_resume` (`{"resume_text":"...","accepted_suggestions":[...]}`)
- `GET /interview_tips?role=...`

Interactive API documentation is available at `/docs` while the API is running.

## Tests and production build

Run the backend service tests from `backend/`:

```powershell
python -m unittest discover -s tests -v
```

Build the frontend from `frontend/` after installing npm dependencies:

```powershell
npm run build
```

`/analyze_job` returns `required_skills`, `preferred_skills`, `soft_skills`, and `technical_skills`. Preferred skills are detected only when they appear in clearly marked preferred/nice-to-have/bonus/desired sections. `/compare` accepts an optional `preferred_skills` array and returns preferred matches and gaps separately. `/upload_resume` also returns a heuristic `extraction_confidence`, `detected_sections`, and `word_count`; review the extracted text when confidence is low or medium. DOCX table text is included. The estimate cannot reliably reconstruct visual layout or identify scanned content.

The edit-resume chat applies explicit quoted replacements, removals, or supplied text additions locally by default. For open-ended AI edits, configure the optional OpenAI integration described below; it sends the current resume and instruction to the configured provider only when `ENABLE_OPENAI_REWRITER=true` and `OPENAI_API_KEY` are set. The editor shows the resulting draft for review and retains its PDF download action.

## Notes

Skill recognition uses spaCy's phrase matcher when available and falls back to a deterministic phrase dictionary. Sentence Transformers is optional: install `backend/requirements-nlp.txt` and cache `all-MiniLM-L6-v2` locally to enable semantic matching. No model download or LLM key is required by the default setup. Scanned-image PDFs need OCR, which is not included. ATS alignment is the matched-required-skill ratio, not a prediction of any employer's proprietary ATS score. Suggestion acceptance adds review notes; it does not invent work history. PDF export formats editable text for download; it does not preserve the uploaded document's original layout.

ATS scoring weighs taxonomy keyword relevance (40%), required skill coverage (30%), preferred skill coverage (10%), section completeness (10%), and text readability (10%). The response shows point contributions; it is an estimate, not a proprietary ATS prediction. The rule-based rewriter preserves source facts and uses explicit placeholders instead of inventing outcome metrics. For optional OpenAI rewriting, install `backend/requirements-openai.txt`, set `OPENAI_API_KEY`, and explicitly opt in with `ENABLE_OPENAI_REWRITER=true`; this sends resume text and the job description to the configured OpenAI service. Learning paths use short, rule-based plans and are not endorsements of a specific course. Before production deployment, configure explicit CORS origins, HTTPS, upload rate limits, structured logging, and a retention/privacy policy that matches your jurisdiction and hosting setup. Uploaded document content is processed in memory and is not persisted by this starter.

The earlier underscore routes `/ats_score`, `/rewrite_resume`, and `/learning_path` remain available as compatibility aliases.
