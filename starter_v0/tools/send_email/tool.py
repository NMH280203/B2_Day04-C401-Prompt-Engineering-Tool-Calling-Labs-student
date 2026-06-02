from __future__ import annotations

import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from tools._shared import TIMEOUT, err


def send_email(
    to: str = "",
    subject: str = "",
    body: str = "",
    cc: str = "",
    confirmed: bool = False,
) -> dict[str, Any]:
    """
    Send an email via SMTP (Gmail by default).
    Requires env vars: EMAIL_SENDER, EMAIL_PASSWORD, and optionally EMAIL_SMTP_HOST / EMAIL_SMTP_PORT.
    Always requires confirmed=True before actually sending.
    """
    if not confirmed:
        return {
            "tool": "send_email",
            "status": "needs_confirmation",
            "preview": {
                "to": to,
                "cc": cc or None,
                "subject": subject,
                "body_preview": body[:200] + ("…" if len(body) > 200 else ""),
            },
            "message": "Chưa gửi — cần xác nhận từ người dùng trước khi gửi email.",
        }

    # Validate required fields
    if not to:
        return {"tool": "send_email", "error": "missing_field", "message": "Thiếu địa chỉ người nhận (to)."}
    if not subject:
        return {"tool": "send_email", "error": "missing_field", "message": "Thiếu tiêu đề email (subject)."}
    if not body:
        return {"tool": "send_email", "error": "missing_field", "message": "Thiếu nội dung email (body)."}

    sender   = os.getenv("EMAIL_SENDER", "")
    password = os.getenv("EMAIL_PASSWORD", "")
    host     = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
    port     = int(os.getenv("EMAIL_SMTP_PORT", "465"))

    if not sender or not password:
        return {
            "tool": "send_email",
            "error": "missing_config",
            "message": "Thiếu EMAIL_SENDER hoặc EMAIL_PASSWORD trong file .env",
        }

    try:
        msg = MIMEMultipart("alternative")
        msg["From"]    = sender
        msg["To"]      = to
        msg["Subject"] = subject
        if cc:
            msg["Cc"] = cc

        # Add plain-text and HTML parts
        msg.attach(MIMEText(body, "plain", "utf-8"))

        recipients = [addr.strip() for addr in to.split(",")]
        if cc:
            recipients += [addr.strip() for addr in cc.split(",")]

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context, timeout=TIMEOUT) as server:
            server.login(sender, password)
            server.sendmail(sender, recipients, msg.as_string())

        return {
            "tool": "send_email",
            "status": "sent",
            "to": to,
            "cc": cc or None,
            "subject": subject,
            "chars_sent": len(body),
        }

    except smtplib.SMTPAuthenticationError:
        return {
            "tool": "send_email",
            "error": "auth_failed",
            "message": "Xác thực SMTP thất bại. Kiểm tra EMAIL_SENDER và EMAIL_PASSWORD. "
                       "Với Gmail, dùng App Password (không phải mật khẩu thường).",
        }
    except Exception as exc:
        return err("send_email", exc)
