"""Orchestration: render the digest and deliver it by email."""

# Builtin imports
from datetime import UTC, datetime

# Local imports
from ..config import AppConfig, Settings
from ..logger import get_logger
from ..models import Item
from .render import render_html, render_subject, render_text
from .sender import send_email

LOG = get_logger(__name__)


def render_digest(ranked: dict[str, list[Item]], now: datetime) -> tuple[str, str, str]:
    """Return (subject, html, text) for the ranked+summarized items."""
    return render_subject(now), render_html(ranked, now), render_text(ranked, now)


def deliver(
    config: AppConfig,
    settings: Settings,
    ranked: dict[str, list[Item]],
    now: datetime | None = None,
) -> None:
    """Render and email the digest. Raises if SMTP credentials are missing."""
    moment = now if now is not None else datetime.now(UTC)
    subject, html, text = render_digest(ranked, moment)

    user = (settings.smtp_user or "").strip()
    # App passwords are shown with spaces; strip them so paste-as-is works.
    password = (settings.smtp_pass or "").replace(" ", "")
    if not user or not password:
        raise ValueError("missing SMTP creds: set SMTP_USER and SMTP_PASS")

    send_email(
        sender=user,
        password=password,
        recipient=config.recipient_email,
        subject=subject,
        html=html,
        text=text,
    )
