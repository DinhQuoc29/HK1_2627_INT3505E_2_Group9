"""Lỗi thống nhất theo RFC 9457 (problem+json), dùng cho mọi module."""
from flask import jsonify, request
from werkzeug.exceptions import HTTPException

PROBLEM_JSON = "application/problem+json"

_TITLES = {
    400: "Bad Request", 401: "Unauthorized", 403: "Forbidden", 404: "Not Found",
    405: "Method Not Allowed", 409: "Conflict", 415: "Unsupported Media Type",
    422: "Unprocessable Content", 429: "Too Many Requests", 500: "Internal Server Error",
    503: "Service Unavailable",
}


class ProblemError(Exception):
    """Lỗi nghiệp vụ/HTTP có cấu trúc. `slug` thành phần cuối của `type`."""

    def __init__(self, status, slug, detail, *, errors=None, headers=None, persist=False):
        super().__init__(detail)
        self.status = status
        self.slug = slug
        self.detail = detail
        self.errors = errors
        self.headers = headers or {}
        self.persist = persist  # True: session_scope commit trước khi trả lỗi

    def to_body(self):
        body = {
            "type": f"/problems/{self.slug}",
            "title": _TITLES.get(self.status, "Error"),
            "status": self.status,
            "detail": self.detail,
            "instance": request.path,
        }
        if self.errors:
            body["errors"] = self.errors
        return body


def problem_response(err: ProblemError):
    resp = jsonify(err.to_body())
    resp.status_code = err.status
    resp.headers["Content-Type"] = PROBLEM_JSON
    for k, v in err.headers.items():
        resp.headers[k] = v
    return resp


def register_error_handlers(app):
    @app.errorhandler(ProblemError)
    def _problem(err):
        return problem_response(err)

    @app.errorhandler(HTTPException)
    def _http(err):
        slug = (err.name or "error").lower().replace(" ", "-")
        return problem_response(ProblemError(err.code or 500, slug, err.description or err.name))

    @app.errorhandler(Exception)
    def _unhandled(err):
        app.logger.exception("unhandled_error")
        return problem_response(ProblemError(500, "internal-error", "Đã có lỗi xảy ra, vui lòng thử lại sau."))
