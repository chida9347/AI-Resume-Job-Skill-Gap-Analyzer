"""Application errors and centralized exception handling."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("roleprint.errors")


class AppError(Exception):
    def __init__(self, status_code: int, message: str, code: str = "error", details=None):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.code = code
        self.details = details


def _payload(message, code: str, details=None, request_id: str | None = None):
    body = {
        # `detail` is retained for compatibility with the existing frontend.
        "detail": message,
        "error": {"code": code, "message": message},
    }
    if details is not None:
        body["error"]["details"] = details
    if request_id:
        body["error"]["request_id"] = request_id
    return body


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload(exc.message, exc.code, exc.details, getattr(request.state, "request_id", None)),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError):
        details = [
            {"field": ".".join(str(part) for part in error.get("loc", [])), "message": error.get("msg", "")}
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_payload("Please check the highlighted fields.", "validation_error", details,
                             getattr(request.state, "request_id", None)),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException):
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload(message, "http_error", None, getattr(request.state, "request_id", None)),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None)
        # Log the stack trace but never the request body (resumes are sensitive).
        logger.exception("Unhandled error request_id=%s path=%s", request_id, request.url.path)
        return JSONResponse(
            status_code=500,
            content=_payload(
                "Something went wrong on our side. Please try again.",
                "internal_error",
                None,
                request_id,
            ),
        )
