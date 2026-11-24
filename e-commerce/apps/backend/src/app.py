"""Application factory. Chạy dev (từ thư mục src/): uvicorn app:create_app --factory --port 5000 --reload"""
import json
import logging
import pathlib

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse

import accounts.model  # noqa: F401  (đăng ký model)
from common.errors import register_error_handlers
from common.ratelimit import SlidingWindowLimiter
from config import Settings

ROOT = pathlib.Path(__file__).resolve().parent.parent


class _JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps(
            {"level": record.levelname, "logger": record.name, "msg": record.getMessage()},
            ensure_ascii=False,
        )


def _setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())
    for name in ("accounts", "app"):
        logger = logging.getLogger(name)
        logger.handlers = [handler]
        logger.setLevel(logging.INFO)


def create_app(**overrides) -> FastAPI:
    import db  # noqa: F401  (nạp .env trước khi đọc cấu hình)

    settings = Settings.from_env(**overrides)
    settings.validate()
    _setup_logging()

    # Tài liệu API là openapi.yaml viết trước (design-first); tắt trang tự sinh để chỉ có một nguồn sự thật.
    app = FastAPI(title="E-commerce API", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings = settings
    app.state.limiter = SlidingWindowLimiter()
    register_error_handlers(app)

    from accounts.routes import router as accounts_router

    app.include_router(accounts_router)

    @app.get("/healthz", include_in_schema=False)
    def healthz():
        return {"status": "ok"}

    @app.get("/api/v1/openapi.yaml", include_in_schema=False)
    def openapi_spec():
        return FileResponse(ROOT / "openapi.yaml", media_type="application/yaml")

    @app.get("/api/v1/docs", include_in_schema=False)
    def swagger_ui():
        return HTMLResponse(
            "<!doctype html><title>API docs</title>"
            '<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">'
            '<div id="ui"></div><script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>'
            '<script>SwaggerUIBundle({url:"/api/v1/openapi.yaml",dom_id:"#ui"})</script>'
        )

    return app
