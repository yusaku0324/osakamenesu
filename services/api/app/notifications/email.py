from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Sequence

from ..settings import settings

logger = logging.getLogger(__name__)


def send_email(subject: str, body: str, recipients: Sequence[str]) -> None:
    """Send a plain-text email notification.

    If SMTP settings or recipients are missing, the function exits silently.
    """

    if not recipients:
        logger.debug("Email notification skipped: no recipients")
        return

    if not settings.notify_smtp_host or not settings.notify_from_email:
        logger.warning("Email notification skipped: SMTP host or from address not configured")
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.notify_from_email
    message["To"] = ", ".join(recipients)
    message.set_content(body)

    host = settings.notify_smtp_host
    port = settings.notify_smtp_port or (465 if settings.notify_smtp_use_ssl else 587)

    try:
        if settings.notify_smtp_use_ssl:
            with smtplib.SMTP_SSL(host, port, timeout=10) as client:
                _login_if_needed(client)
                client.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=10) as client:
                if settings.notify_smtp_use_tls:
                    client.starttls()
                _login_if_needed(client)
                client.send_message(message)
    except Exception:
        logger.exception("Failed to send notification email")


def _login_if_needed(client: smtplib.SMTP) -> None:
    username = settings.notify_smtp_username
    password = settings.notify_smtp_password
    if username and password:
        client.login(username, password)
