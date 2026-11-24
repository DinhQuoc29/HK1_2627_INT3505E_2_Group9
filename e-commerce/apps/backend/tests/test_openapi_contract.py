"""Hợp đồng OpenAPI: spec hợp lệ, mọi route đã cài đặt đều được mô tả, và phần Accounts khớp 100%."""
import pathlib

import pytest
import yaml
from openapi_spec_validator import validate

from app import create_app

SPEC_PATH = pathlib.Path(__file__).resolve().parent.parent / "openapi.yaml"
IMPLEMENTED_TAGS = {"users", "auth", "shops", "admin", "sellers"}  # thêm tag vào đây khi cài đặt xong module tương ứng
HTTP = {"get", "post", "put", "patch", "delete"}


@pytest.fixture(scope="module")
def spec():
    return yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def implemented():
    # Route thật của ứng dụng (lấy từ lược đồ FastAPI sinh từ code, không phải openapi.yaml viết tay).
    paths = create_app().openapi()["paths"]
    return {(m, path) for path, item in paths.items() if path.startswith("/api/v1/") for m in item if m in HTTP}


def _documented(spec, only_tags=None):
    return {
        (m, path)
        for path, item in spec["paths"].items()
        for m, op in item.items()
        if m in HTTP and (only_tags is None or set(op.get("tags", [])) & only_tags)
    }


def test_spec_is_valid_openapi(spec):
    validate(spec)


def test_every_implemented_route_is_documented(spec, implemented):
    assert implemented - _documented(spec) == set()


def test_documented_routes_of_implemented_modules_exist(spec, implemented):
    assert _documented(spec, IMPLEMENTED_TAGS) - implemented == set()


def test_error_responses_are_problem_json(spec):
    for path, item in spec["paths"].items():
        for m, op in item.items():
            if m not in HTTP:
                continue
            for code, resp in op["responses"].items():
                if code.startswith(("4", "5")) and "$ref" not in resp:
                    assert "application/problem+json" in resp.get("content", {}), f"{m} {path} {code}"
