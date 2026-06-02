from __future__ import annotations

import os
import re
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from tools._shared import TIMEOUT, err

# RFC-5322 simplified — catches most typos (missing @, missing domain, spaces…)
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)


def _validate_addresses(raw: str) -> list[str]:
    """Return list of invalid addresses found in a comma-separated string."""
    bad = []
    for addr in raw.split(","):
        addr = addr.strip()
        if addr and not _EMAIL_RE.match(addr):
            bad.append(addr)
    return bad


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
    Validates email format before sending; returns invalid_email error if address is malformed.
    """

    # ── Validate email format FIRST (before confirmation check) ──────────────
    if to:
        bad_to = _validate_addresses(to)
        if bad_to:
            return {
                "tool": "send_email",
                "error": "invalid_email",
                "invalid_addresses": bad_to,
                "message": (
                    f"Địa chỉ email không hợp lệ: {', '.join(bad_to)}. "
                    "Vui lòng kiểm tra lại (phải có dạng user@domain.com)."
                ),
                "action_required": "ask_user_to_correct_email",
            }

    if cc:
        bad_cc = _validate_addresses(cc)
        if bad_cc:
            return {
                "tool": "send_email",
                "error": "invalid_email",
                "invalid_addresses": bad_cc,
                "field": "cc",
                "message": (
                    f"Địa chỉ CC không hợp lệ: {', '.join(bad_cc)}. "
                    "Vui lòng kiểm tra lại."
                ),
                "action_required": "ask_user_to_correct_email",
            }

    # ── Confirmation gate ────────────────────────────────────────────────────
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

    # ── Validate required fields ─────────────────────────────────────────────
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

    except smtplib.SMTPRecipientsRefused as exc:
        # Server rejected one or more recipients — address doesn't exist
        refused = list(exc.recipients.keys())
        return {
            "tool": "send_email",
            "error": "recipient_refused",
            "refused_addresses": refused,
            "message": (
                f"Máy chủ từ chối địa chỉ: {', '.join(refused)}. "
                "Địa chỉ email có thể không tồn tại."
            ),
            "action_required": "ask_user_to_correct_email",
        }

    except smtplib.SMTPAuthenticationError:
        return {
            "tool": "send_email",
            "error": "auth_failed",
            "message": (
                "Xác thực SMTP thất bại. Kiểm tra EMAIL_SENDER và EMAIL_PASSWORD. "
                "Với Gmail, dùng App Password (không phải mật khẩu thường)."
            ),
        }

    except Exception as exc:
        return err("send_email", exc)
