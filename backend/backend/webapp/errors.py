from __future__ import annotations

from typing import Any, Mapping

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


_DEFAULT_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "validation_error",
    429: "rate_limited",
    500: "internal_error",
    503: "service_unavailable",
}


def _request_id(request: Request) -> str:
    return str(
        getattr(request.state, "request_id", None)
        or request.headers.get("X-Request-ID")
        or "-"
    )


def _message_from_detail(detail: Any, fallback: str) -> str:
    if isinstance(detail, str) and detail.strip():
        return detail
    if isinstance(detail, Mapping):
        for key in ("message", "detail", "error"):
            value = detail.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return fallback


def error_response(
    request: Request,
    *,
    status_code: int,
    detail: Any,
    code: str | None = None,
    fallback_message: str = "Request failed",
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    message = _message_from_detail(detail, fallback_message)
    request_id = _request_id(request)
    error: dict[str, Any] = {
        "code": code or _DEFAULT_CODES.get(status_code, "request_failed"),
        "message": message,
        "status": status_code,
        "request_id": request_id,
    }
    if detail != message:
        error["details"] = detail

    response_headers = {"X-Request-ID": request_id}
    if headers:
        response_headers.update(headers)

    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder({"detail": message, "error": error}),
        headers=response_headers,
    )
