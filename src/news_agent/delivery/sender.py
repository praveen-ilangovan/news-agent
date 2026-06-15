"""SMTP sending via Gmail (SMTP_SSL)."""

# Builtin imports
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Local imports
from ..logger import get_logger

LOG = get_logger(__name__)

_GMAIL_HOST = "smtp.gmail.com"
_GMAIL_PORT = 465


def send_email(
    *,
    sender: str,
    password: str,
    recipient: str,
    subject: str,
    html: str,
    text: str,
) -> None:
    """Send a multipart (text + HTML) email through Gmail SMTP over SSL."""
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    # Plain part first; clients prefer the last alternative (HTML).
    message.attach(MIMEText(text, "plain", "utf-8"))
    message.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP_SSL(_GMAIL_HOST, _GMAIL_PORT) as server:
        server.login(sender, password)
        server.send_message(message)
    LOG.info("email sent", recipient=recipient)
