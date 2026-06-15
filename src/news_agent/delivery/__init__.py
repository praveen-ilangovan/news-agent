"""Delivery: render the digest as HTML/text and send it via email.

Public surface: `render_digest` (pure) and `deliver` (sends via SMTP).
"""

# Local imports
from .service import deliver, render_digest

__all__ = ["deliver", "render_digest"]
