"""Application factory (xem slide B7). Chạy dev: `flask --app app run` từ thư mục src/."""
import json
import logging
import pathlib

from flask import Flask, jsonify, send_file
from flask_jwt_extended import JWTManager

import accounts.model  # noqa: F401  (đăng ký model)
from common.errors import ProblemError, problem_response, register_error_handlers
from config import Config

ROOT = pathlib.Path(__file__).resolve().parent.parent


class _JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps(
            {"level": record.levelname, "logger": record.name, "msg": record.getMessage()},
            ensure_ascii=False,
        )


def create_app(overrides: dict | None = None) -> Flask:
    import db  # noqa: F401  (nạp .env trước khi đọc Config)

    app = Flask(__name__)
    cfg = Config()
    app.config.from_mapping(vars(cfg))
    if overrides:
        app.config.update(overrides)
    if len(app.config["JWT_SECRET_KEY"]) < 32:
        Config.validate(cfg)

    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())
    logging.getLogger("accounts").handlers = [handler]
    logging.getLogger("accounts").setLevel(logging.INFO)

    jwt = JWTManager(app)

    @jwt.expired_token_loader
    def _expired(_h, _p):
        return problem_response(ProblemError(401, "token-expired", "Access token đã hết hạn."))

    @jwt.invalid_token_loader
    def _invalid(_reason):
        return problem_response(ProblemError(401, "invalid-token", "Token không hợp lệ."))

    @jwt.unauthorized_loader
    def _missing(_reason):
        return problem_response(
            ProblemError(401, "missing-token", "Cần đăng nhập.", headers={"WWW-Authenticate": "Bearer"})
        )

    register_error_handlers(app)

    from accounts.routes import bp as accounts_bp

    app.register_blueprint(accounts_bp)

    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok")

    @app.get("/api/v1/openapi.yaml")
    def openapi_spec():
        return send_file(ROOT / "openapi.yaml", mimetype="application/yaml")

    @app.get("/api/v1/docs")
    def swagger_ui():
        return (
            "<!doctype html><title>API docs</title>"
            '<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">'
            '<div id="ui"></div><script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>'
            '<script>SwaggerUIBundle({url:"/api/v1/openapi.yaml",dom_id:"#ui"})</script>'
        )

    return app

