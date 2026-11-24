"""Schema (Marshmallow) cho request/response của Accounts. Field nhạy cảm không bao giờ ra API."""
from marshmallow import Schema, ValidationError, fields, validate, validates, pre_load

from common.errors import ProblemError


def _password_rules(value: str):
    if len(value.encode("utf-8")) > 72:  # giới hạn của bcrypt
        raise ValidationError("Mật khẩu tối đa 72 byte.")
    if not (any(c.isalpha() for c in value) and any(c.isdigit() for c in value)):
        raise ValidationError("Mật khẩu cần có cả chữ và số.")


class _EmailMixin:
    @pre_load
    def _normalize_email(self, data, **_):
        if isinstance(data, dict) and isinstance(data.get("email"), str):
            data = {**data, "email": data["email"].strip().lower()}
        return data


class RegisterSchema(_EmailMixin, Schema):
    email = fields.Email(required=True, validate=validate.Length(max=255))
    password = fields.Str(required=True, validate=[validate.Length(min=8, max=128), _password_rules])
    full_name = fields.Str(required=True)

    @pre_load
    def _strip_name(self, data, **_):
        if isinstance(data, dict) and isinstance(data.get("full_name"), str):
            data = {**data, "full_name": data["full_name"].strip()}
        return data

    @validates("full_name")
    def _name_len(self, value, **_):
        if not 1 <= len(value) <= 100:
            raise ValidationError("Họ tên từ 1 đến 100 ký tự.")


class LoginSchema(_EmailMixin, Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=1, max=128))


class GoogleLoginSchema(Schema):
    credential = fields.Str(required=True, validate=validate.Length(min=1, max=4096))


class UserSchema(Schema):
    id = fields.UUID()
    email = fields.Str()
    full_name = fields.Str()
    role = fields.Str()
    created_at = fields.DateTime()


def load_body(schema: Schema, data):
    """Validate body; lỗi trả 422 problem+json kèm danh sách lỗi theo field."""
    if not isinstance(data, dict):
        raise ProblemError(400, "invalid-json", "Body phải là một JSON object.")
    try:
        return schema.load(data)
    except ValidationError as exc:
        errors = [
            {"field": field, "message": msg}
            for field, msgs in exc.normalized_messages().items()
            for msg in (msgs if isinstance(msgs, list) else [str(msgs)])
        ]
        raise ProblemError(422, "validation-error", "Dữ liệu gửi lên không hợp lệ.", errors=errors)
