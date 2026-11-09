# Deployment Guide

This guide covers a production deployment of Roleprint: a FastAPI API, a
React/Vite SPA served by nginx, and PostgreSQL. It assumes Docker Compose or an
equivalent container platform. Read [`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md)
before promising accuracy or scale.

---

## 1. Production checklist

- [ ] Set `ENVIRONMENT=production`.
- [ ] Set a strong, unique `JWT_SECRET` (48+ random bytes).
- [ ] Set `AUTO_CREATE_TABLES=false` and run `alembic upgrade head`.
- [ ] Use PostgreSQL via `DATABASE_URL=postgresql+psycopg://...`.
- [ ] Set `CORS_ORIGINS` to the exact public frontend origin(s). Do not use `*`.
- [ ] Keep `ENABLE_RATE_LIMIT=true`.
- [ ] Terminate TLS at a reverse proxy or load balancer.
- [ ] Set `VITE_API_URL=/api` for the nginx-proxied build.
- [ ] Configure database backups and retention.
- [ ] Decide whether OpenAI, semantic matching and OCR are enabled. Default: off.
- [ ] Review the privacy policy for your jurisdiction and hosting region.
- [ ] Set log aggregation and alerting on `/health`.

Generate a secret:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## 2. Docker Compose

```powershell
Copy-Item .env.example .env
# Set JWT_SECRET and POSTGRES_PASSWORD in .env.
docker compose up --build -d
docker compose ps
docker compose logs -f backend
```

Services:

| Service | Port | Notes |
| --- | --- | --- |
| `db` | internal | PostgreSQL 16, named volume `db_data`. |
| `backend` | `8000` | Runs `alembic upgrade head` then uvicorn. |
| `frontend` | `8080` | nginx serves the SPA and proxies `/api/` to `backend:8000`. |

The frontend is the intended entry point. You can remove the backend port
mapping if you do not need direct API access.

### Migrations

Compose runs migrations on every start. For controlled releases, run them as a
separate one-shot job instead:

```powershell
docker compose run --rm backend alembic upgrade head
```

Take a database backup before applying migrations that alter or drop columns.

### Updating

```powershell
git pull
docker compose build
docker compose run --rm backend alembic upgrade head
docker compose up -d
```

---

## 3. Reverse proxy and TLS

Put nginx, Caddy, Traefik or a cloud load balancer in front of the frontend
container. Requirements:

- HTTPS with a valid certificate and HTTP→HTTPS redirect.
- Forward `X-Forwarded-For` and `X-Forwarded-Proto`.
- Allow request bodies up to the configured upload limit (12 MB at the proxy,
  10 MB in the API by default).
- Do not cache `/api/` responses.
- Add security headers: `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`,
  and a Content-Security-Policy that permits your asset origins.

The frontend image already proxies `/api/` to the backend and falls back to
`index.html` for client-side routes.

---

## 4. Environment reference

See [`.env.example`](../.env.example) for the full list. Production essentials:

```dotenv
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql+psycopg://roleprint:STRONG_PASSWORD@db:5432/roleprint
AUTO_CREATE_TABLES=false
JWT_SECRET=REPLACE_WITH_A_LONG_RANDOM_SECRET
CORS_ORIGINS=https://resume.example.com
ENABLE_RATE_LIMIT=true
ENABLE_SEMANTIC_MATCHING=true
ENABLE_OPENAI_REWRITER=false
ENABLE_OCR=false
```

The API warns at startup if the development JWT secret is still in use. Treat
that warning as a deployment blocker.

---

## 5. Database operations

### Backup

```powershell
docker compose exec -T db pg_dump -U roleprint roleprint > roleprint-backup.sql
```

### Restore

```powershell
Get-Content roleprint-backup.sql | docker compose exec -T db psql -U roleprint roleprint
```

### Retention

Saved data is user-controlled through Settings (export, clear history, delete
account). Define a retention policy for backups and logs. Backups contain
personal data and must be encrypted at rest and access-controlled.

### Schema changes

```powershell
cd backend
alembic revision --autogenerate -m "add field"
# Review the generated file before committing.
alembic upgrade head
```

Never rely on `AUTO_CREATE_TABLES=true` in production.

---

## 6. Scaling and operations

The current design is a modular monolith:

- The rate limiter is **in-memory per process**. With multiple API workers or
  replicas, limits are per instance. Use a shared limiter (Redis) before scaling
  horizontally if strict global limits are required.
- Analysis is CPU-bound. Increase workers or replicas for throughput; keep
  request timeouts above the expected analysis time.
- The semantic model loads per process and consumes memory. Size containers
  accordingly or leave semantic matching disabled.
- Health endpoint: `GET /health` returns status, version, environment and
  feature flags. Use it for container and load-balancer probes.
- Logs are structured JSON to stdout with request IDs. Do not log raw resume
  text; the application does not.
- There is no background job queue. Long OpenAI calls run inside the request.

---

## 7. Optional features

### OpenAI rewriting

```dotenv
ENABLE_OPENAI_REWRITER=true
OPENAI_API_KEY=sk-...
OPENAI_CONSENT_DEFAULT=false
```

Keep per-request consent enabled unless your privacy policy explicitly covers
sending resume and job text to the provider. Install `requirements-openai.txt`
in the image if you enable this (the default image does not).

### Semantic matching

Install `requirements-nlp.txt`, provision a cached sentence-transformers model,
and keep `ENABLE_SEMANTIC_MATCHING=true`. The app never downloads models
implicitly. Semantic-only matches are reported as `partial`, never as proven
experience.

### OCR

Install `requirements-optional.txt` and the Tesseract binary, then set
`ENABLE_OCR=true`. Without it, scanned PDFs return a clear error.

---

## 8. Rollback

1. Stop the stack.
2. Restore the previous application image/tag.
3. Roll back the database only if the new revision is reversible:
   `alembic downgrade -1`.
4. Restore the database backup if a downgrade is unsafe.
5. Restart and verify `/health`.

Keep migrations backward-compatible for one release where possible.

---

## 9. Post-deployment verification

```powershell
curl https://resume.example.com/api/health
```

Then, in the browser:

1. Run an anonymous analysis from paste and from upload.
2. Register an account and confirm login and refresh.
3. Save an analysis, reopen it from history, export data, clear history.
4. Delete the test account.
5. Confirm errors include a request ID and no resume text appears in logs.

---

## 10. Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Backend exits at startup | `JWT_SECRET` missing in Compose | Set it in `.env`. |
| `relation does not exist` | Migrations not applied | Run `alembic upgrade head`. |
| CORS error in browser | Origin not in `CORS_ORIGINS` | Add the exact scheme/host/port. |
| 413 on upload | Proxy body limit | Raise `client_max_body_size`. |
| SPA routes 404 | Missing history fallback | Keep the nginx `try_files` rule. |
| Semantic matching silently lexical | No cached model | Install and provision the model, or accept the fallback. |
