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
- `POST /learning-path` (`{"missing_skills":[...]}`)
- `POST /suggestions` (`{"missing_skills":[...],"resume_text":"..."}`)
- `POST /update_resume` (`{"resume_text":"...","accepted_suggestions":[...]}`)
- `GET /interview_tips?role=...`

Interactive API documentation is available at `/docs` while the API is running.

## Notes

Skill recognition uses spaCy's phrase matcher when available and falls back to a deterministic phrase dictionary. Sentence Transformers is optional: install `backend/requirements-nlp.txt` and cache `all-MiniLM-L6-v2` locally to enable semantic matching. No model download or LLM key is required by the default setup. Scanned-image PDFs need OCR, which is not included. ATS alignment is the matched-required-skill ratio, not a prediction of any employer's proprietary ATS score. Suggestion acceptance adds review notes; it does not invent work history. PDF export formats editable text for download; it does not preserve the uploaded document's original layout.

ATS scoring weights keyword overlap (60%), section completeness (25%), and basic text-format heuristics (15%); it is an estimate, not a proprietary ATS prediction. The rule-based rewriter preserves source facts and uses explicit placeholders instead of inventing outcome metrics. For optional OpenAI rewriting, install `backend/requirements-openai.txt`, set `OPENAI_API_KEY`, and explicitly opt in with `ENABLE_OPENAI_REWRITER=true`; this sends resume text and the job description to the configured OpenAI service. Learning paths use short, rule-based plans and are not endorsements of a specific course. Before production deployment, configure explicit CORS origins, HTTPS, upload rate limits, structured logging, and a retention/privacy policy that matches your jurisdiction and hosting setup. Uploaded document content is processed in memory and is not persisted by this starter.

The earlier underscore routes `/ats_score`, `/rewrite_resume`, and `/learning_path` remain available as compatibility aliases.