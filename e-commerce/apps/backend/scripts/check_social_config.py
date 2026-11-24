"""Kiểm tra cấu hình đăng nhập Google / Facebook (luồng thật). Không in bí mật.

    cd apps/backend && .venv/bin/python scripts/check_social_config.py

Chỉ gọi mạng cho nhà cung cấp đã được cấu hình:
  - Google: tải chứng chỉ công khai (không gửi dữ liệu nào của bạn).
  - Facebook: hỏi Graph API tên app bằng app token "APP_ID|APP_SECRET" (cách chính thức để kiểm tra cặp ID/secret).
Thoát với mã 1 nếu có nhà cung cấp cấu hình nhưng sai.
"""
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import requests  # noqa: E402

import db  # noqa: E402,F401  (nạp .env)

WEB_ENV = pathlib.Path(__file__).resolve().parents[2] / "web" / ".env"  # apps/web/.env
GRAPH = "https://graph.facebook.com/v21.0"
failed = False


def line(ok, text):
    global failed
    mark = {True: "✔", False: "✘", None: "–"}[ok]
    if ok is False:
        failed = True
    print(f" {mark} {text}")


def web_env() -> dict:
    path = WEB_ENV
    out = {}
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            if "=" in raw and not raw.lstrip().startswith("#"):
                k, v = raw.split("=", 1)
                out[k.strip()] = v.strip()
    return out


def check_google(web):
    print("Google")
    cid = os.getenv("GOOGLE_CLIENT_ID", "")
    if not cid:
        return line(None, "chưa cấu hình (GOOGLE_CLIENT_ID trống) – nút Google sẽ mờ")
    line(cid.endswith(".apps.googleusercontent.com"), "GOOGLE_CLIENT_ID có dạng *.apps.googleusercontent.com")
    line(web.get("VITE_GOOGLE_CLIENT_ID") == cid, "VITE_GOOGLE_CLIENT_ID (apps/web/.env) trùng GOOGLE_CLIENT_ID")
    try:
        r = requests.get("https://www.googleapis.com/oauth2/v3/certs", timeout=5)
        line(r.status_code == 200 and bool(r.json().get("keys")), "tải được chứng chỉ công khai của Google (backend xác minh được token)")
    except requests.RequestException as exc:
        line(False, f"không kết nối được Google: {exc.__class__.__name__}")
    print("   Nhắc: trong Google Cloud Console, Authorized JavaScript origins phải có đúng http://localhost:5173")


def check_facebook(web):
    print("Facebook")
    app_id, secret = os.getenv("FACEBOOK_APP_ID", ""), os.getenv("FACEBOOK_APP_SECRET", "")
    if not app_id and not secret:
        return line(None, "chưa cấu hình (FACEBOOK_APP_ID/SECRET trống) – nút Facebook sẽ mờ")
    line(bool(re.fullmatch(r"\d{6,20}", app_id)), "FACEBOOK_APP_ID là chuỗi số")
    line(bool(secret), "FACEBOOK_APP_SECRET đã đặt (không hiển thị)")
    line(web.get("VITE_FACEBOOK_APP_ID") == app_id, "VITE_FACEBOOK_APP_ID (apps/web/.env) trùng FACEBOOK_APP_ID")
    if not (app_id and secret):
        return
    try:
        r = requests.get(f"{GRAPH}/{app_id}", params={"fields": "id,name", "access_token": f"{app_id}|{secret}"}, timeout=5)
        if r.status_code == 200 and r.json().get("id") == app_id:
            line(True, f"Facebook xác nhận cặp ID/secret (app: {r.json().get('name')!r})")
        else:
            line(False, f"Facebook từ chối cặp ID/secret (HTTP {r.status_code}): kiểm tra lại App Secret")
    except requests.RequestException as exc:
        line(False, f"không kết nối được Facebook: {exc.__class__.__name__}")
    print("   Nhắc: Facebook Login → Cài đặt: bật \"Đăng nhập bằng JavaScript SDK\" và thêm http://localhost:5173/ vào \"Miền được phép cho JavaScript SDK\" (không dùng App Domains, Meta không nhận localhost).")
    print("   Nhắc: app ở chế độ Development thì chỉ tài khoản có vai trò trong app mới đăng nhập được.")


def main():
    web = web_env()
    check_google(web)
    check_facebook(web)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
