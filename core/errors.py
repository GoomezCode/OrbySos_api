import uuid

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

_STATUS_DEFAULT_CODES = {
    400: "BAD_REQUEST",
    401: "AUTH_UNAUTHORIZED",
    403: "AUTH_FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    500: "INTERNAL_ERROR",
    503: "SERVICE_UNAVAILABLE",
}


def _trace_id() -> str:
    return f"trace-{uuid.uuid4().hex[:12]}"


def _error_payload(error: dict) -> dict:
    return {"error": error, "trace_id": _trace_id()}


def make_error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=_error_payload({"code": code, "message": message}),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict):
        error = dict(detail)
    else:
        error = {
            "code": _STATUS_DEFAULT_CODES.get(exc.status_code, f"HTTP_{exc.status_code}"),
            "message": str(detail),
        }
    return JSONResponse(status_code=exc.status_code, content=_error_payload(error))


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    fields = []
    for err in exc.errors():
        loc = list(err.get("loc") or [])
        field = ".".join(str(part) for part in loc if part not in ("body", "query", "path", "header"))
        fields.append({"field": field or "body", "message": err.get("msg", "Valor inválido.")})
    error = {"code": "VALIDATION_ERROR", "message": "Revise os campos indicados.", "fields": fields}
    return JSONResponse(status_code=422, content=_error_payload(error))


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    error = {
        "code": "INTERNAL_ERROR",
        "message": "Erro interno inesperado. Tente novamente em instantes.",
    }
    return JSONResponse(status_code=500, content=_error_payload(error))