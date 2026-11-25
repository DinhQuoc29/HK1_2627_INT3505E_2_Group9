"""Gửi email. Backend chọn bằng EMAIL_BACKEND: console (log, mặc định dev), smtp, memory (test).

Gửi chạy nền sau khi trả response (FastAPI BackgroundTasks) nên SMTP chậm không làm chậm API;
lỗi gửi chỉ ghi log, không làm hỏng request (người dùng có thể bấm gửi lại).
"""
import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from config import Settings

log = logging.getLogger("app")


@dataclass
class Mail:
    to: str
    subject: str
    text: str
    html: str | None = None


class Mailer:
    def send(self, mail: Mail) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class ConsoleMailer(Mailer):
    """Dev: in nội dung ra log để lấy link mà không cần SMTP."""

    def send(self, mail: Mail) -> None:
        log.info("EMAIL to=%s subject=%s\n%s", mail.to, mail.subject, mail.text)


class MemoryMailer(Mailer):
    """Test: giữ thư trong bộ nhớ."""

    def __init__(self) -> None:
        self.outbox: list[Mail] = []

    def send(self, mail: Mail) -> None:
        self.outbox.append(mail)


class SmtpMailer(Mailer):
    def __init__(self, st: Settings) -> None:
        self.st = st

    def send(self, mail: Mail) -> None:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = self.st.email_from, mail.to, mail.subject
        msg.set_content(mail.text)
        if mail.html:
            msg.add_alternative(mail.html, subtype="html")
        try:
            with smtplib.SMTP(self.st.smtp_host, self.st.smtp_port, timeout=10) as smtp:
                if self.st.smtp_starttls:
                    smtp.starttls()
                if self.st.smtp_user:
                    smtp.login(self.st.smtp_user, self.st.smtp_password)
                smtp.send_message(msg)
        except (OSError, smtplib.SMTPException):
            log.exception("email_send_failed to=%s subject=%s", mail.to, mail.subject)


def build_mailer(st: Settings) -> Mailer:
    return {"smtp": SmtpMailer, "memory": lambda _: MemoryMailer()}.get(st.email_backend, lambda _: ConsoleMailer())(st)
