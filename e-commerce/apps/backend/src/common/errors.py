"""Lỗi thống nhất theo RFC 9457 (problem+json), dùng cho mọi module."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM_JSON = "application/problem+json"
log = logging.getLogger("app")

_TITLES = {
    400: "Bad Request", 401: "Unauthorized", 403: "Forbidden", 404: "Not Found",
    405: "Method Not Allowed", 409: "Conflict", 415: "Unsupported Media Type",
    422: "Unprocessable Content", 429: "Too Many Requests", 500: "Internal Server Error",
    503: "Service Unavailable",
}


class ProblemError(Exception):
    """Lỗi nghiệp vụ/HTTP có cấu trúc. `slug` là thành phần cuối của `type`."""

    def __init__(self, status, slug, detail, *, errors=None, headers=None, persist=False):
        super().__init__(detail)
        self.status = status
        self.slug = slug
        self.detail = detail
        self.errors = errors
        self.headers = headers or {}
        self.persist = persist  # True: session_scope commit trước khi trả lỗi


def problem_response(err: ProblemError, request: Request) -> JSONResponse:
    body = {
        "type": f"/problems/{err.slug}",
        "title": _TITLES.get(err.status, "Error"),
        "status": err.status,
        "detail": err.detail,
        "instance": request.url.path,
    }
    if err.errors:
        body["errors"] = err.errors
    return JSONResponse(body, status_code=err.status, headers=err.headers, media_type=PROBLEM_JSON)


def _field_message(e: dict) -> str:
    kind, msg = e.get("type", ""), e.get("msg", "")
    if kind == "missing":
        return "Trường này là bắt buộc."
    if kind == "extra_forbidden":
        return "Trường này không được hỗ trợ."
    if kind in ("string_type", "int_type"):
        return "Kiểu dữ liệu không hợp lệ."
    return msg.removeprefix("Value error, ")  # thông điệp từ validator tự viết


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProblemError)
    async def _problem(request: Request, err: ProblemError):
        return problem_response(err, request)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        # JSON hỏng hoặc body không phải object: lỗi cú pháp (400), không phải lỗi dữ liệu (422).
        if any(e["type"] == "json_invalid" or tuple(e["loc"]) == ("body",) for e in errors):
            return problem_response(
                ProblemError(400, "invalid-json", "Body phải là một JSON object hợp lệ (Content-Type: application/json)."),
                request,
            )
        fields = [
            {"field": ".".join(str(p) for p in e["loc"][1:]), "message": _field_message(e)}
            for e in errors
        ]
        return problem_response(
            ProblemError(422, "validation-error", "Dữ liệu gửi lên không hợp lệ.", errors=fields), request
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        slug = _TITLES.get(exc.status_code, "error").lower().replace(" ", "-")
        return problem_response(
            ProblemError(exc.status_code, slug, str(exc.detail), headers=dict(exc.headers or {})), request
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        log.exception("unhandled_error")
        return problem_response(
            ProblemError(500, "internal-error", "Đã có lỗi xảy ra, vui lòng thử lại sau."), request
        )
