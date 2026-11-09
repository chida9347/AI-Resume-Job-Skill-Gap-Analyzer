# Roleprint API image.
#
# Build from the repository root:
#   docker build -t roleprint-api ./backend
#
# The image installs only the core requirements. Optional extras (OpenAI,
# local sentence-transformers models, OCR) are deliberately excluded so the
# container stays reproducible and works without network access at runtime.

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# curl is used by the container healthcheck only.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as a non-root user. /app must stay writable for the SQLite fallback and
# for Alembic's temporary files when a SQLite database is used.
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

# Compose overrides this command to run `alembic upgrade head` first.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
