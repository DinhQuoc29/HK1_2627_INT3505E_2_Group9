"""Nội dung email của Accounts và Sellers (tiếng Việt, văn bản thuần + HTML tối giản)."""
from html import escape

from config import Settings
from mailer import Mail


def _wrap(text_lines: list[str], link: str | None, button: str | None) -> tuple[str, str]:
    text = "\n\n".join(text_lines + ([f"{button}: {link}"] if link else [])) + "\n\n— E-Market"
    body = "".join(f"<p>{escape(t)}</p>" for t in text_lines)
    if link:
        body += f'<p><a href="{escape(link)}" style="background:#4f46e5;color:#fff;padding:10px 18px;border-radius:8px;text-decoration:none">{escape(button)}</a></p><p style="color:#666;font-size:12px">Nếu nút không bấm được, hãy dán liên kết này vào trình duyệt:<br>{escape(link)}</p>'
    return text, f"<div style='font-family:sans-serif'>{body}<p>— E-Market</p></div>"


def verification_email(st: Settings, to: str, name: str, token: str) -> Mail:
    link = f"{st.app_base_url}/verify-email?token={token}"
    text, html = _wrap(
        [f"Chào {name},", f"Vui lòng xác minh email để hoàn tất tài khoản. Liên kết có hiệu lực {st.verify_token_hours} giờ."],
        link, "Xác minh email",
    )
    return Mail(to, "Xác minh email của bạn", text, html)


def reset_password_email(st: Settings, to: str, name: str, token: str) -> Mail:
    link = f"{st.app_base_url}/reset-password?token={token}"
    text, html = _wrap(
        [f"Chào {name},", f"Chúng tôi nhận được yêu cầu đặt lại mật khẩu. Liên kết có hiệu lực {st.reset_token_minutes} phút và chỉ dùng một lần.",
         "Nếu không phải bạn yêu cầu, hãy bỏ qua email này; mật khẩu của bạn vẫn an toàn."],
        link, "Đặt lại mật khẩu",
    )
    return Mail(to, "Đặt lại mật khẩu", text, html)


def application_submitted_email(st: Settings, to: str, name: str, shop_name: str) -> Mail:
    text, html = _wrap(
        [f"Chào {name},", f"Chúng tôi đã nhận hồ sơ mở shop \"{shop_name}\". Hồ sơ đang chờ duyệt.",
         "Bạn sẽ nhận email khi quản trị viên xử lý hồ sơ."],
        f"{st.app_base_url}/seller/register", "Xem trạng thái hồ sơ",
    )
    return Mail(to, "Đã nhận hồ sơ đăng ký bán hàng", text, html)


def application_approved_email(st: Settings, to: str, name: str, shop_name: str) -> Mail:
    link = f"{st.app_base_url}/seller"
    text, html = _wrap([f"Chào {name},", f"Hồ sơ mở shop \"{shop_name}\" của bạn đã được duyệt. Bạn có thể bắt đầu bán hàng ngay."], link, "Vào kênh người bán")
    return Mail(to, "Hồ sơ người bán đã được duyệt", text, html)


def application_rejected_email(st: Settings, to: str, name: str, shop_name: str, reason: str) -> Mail:
    link = f"{st.app_base_url}/seller/register"
    text, html = _wrap(
        [f"Chào {name},", f"Hồ sơ mở shop \"{shop_name}\" chưa được duyệt.", f"Lý do: {reason}", "Bạn có thể chỉnh sửa và nộp lại hồ sơ."],
        link, "Nộp lại hồ sơ",
    )
    return Mail(to, "Hồ sơ người bán chưa được duyệt", text, html)
