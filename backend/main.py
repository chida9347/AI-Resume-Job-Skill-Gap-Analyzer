"""Application entry point.

Run locally with::

    uvicorn main:app --reload --port 8000

Configuration is environment-driven; see ``.env.example``.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import init_db
from errors import install_error_handlers
from middleware import RateLimitMiddleware, RequestContextMiddleware, configure_logging
from routes.analyzer import router as analysis_router
from routes.auth import router as auth_router
from routes.history import router as history_router

logger = logging.getLogger("roleprint")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    init_db()
    if settings.using_default_secret:
        logger.warning(
            "JWT_SECRET is using the development default. Set a strong secret before deploying."
        )
    logger.info(
        "Roleprint started env=%s database=%s semantic=%s openai=%s ocr=%s",
        settings.environment,
        "sqlite" if settings.database_url.startswith("sqlite") else "external",
        settings.enable_semantic_matching,
        settings.openai_enabled,
        settings.enable_ocr,
    )
    yield
    logger.info("Roleprint stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Explainable resume-to-job alignment, skill-gap analysis, learning roadmaps "
            "and interview preparation. Scores are estimates, not employer ATS results."
        ),
        lifespan=lifespan,
    )

    # Middleware executes in reverse registration order: request context wraps
    # the rate limiter so rejected requests are still logged with an ID.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    application.add_middleware(RateLimitMiddleware)
    application.add_middleware(RequestContextMiddleware)

    install_error_handlers(application)

    application.include_router(auth_router)
    application.include_router(history_router)
    application.include_router(analysis_router)

    @application.get("/health", tags=["meta"])
    async def health() -> dict:
        return {
            "status": "ok",
            "version": settings.app_version,
            "environment": settings.environment,
            "features": {
                "semantic_matching": settings.enable_semantic_matching,
                "openai_rewriter": settings.openai_enabled,
                "ocr": settings.enable_ocr,
            },
        }

    @application.get("/", tags=["meta"])
    async def root() -> dict:
        return {
            "name": "Roleprint",
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health",
        }

    return application


app = create_app()
