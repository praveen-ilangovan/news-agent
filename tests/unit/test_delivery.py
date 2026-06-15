# Builtin imports
from datetime import UTC, datetime
from typing import Any

# Project specific imports
import pytest

# Local imports
from news_agent.config import AppConfig, Settings
from news_agent.delivery.render import render_html, render_subject, render_text
from news_agent.delivery.service import deliver
from news_agent.models import Item

_NOW = datetime(2026, 6, 15, 14, 0, tzinfo=UTC)


def _item(title: str, **kw: Any) -> Item:
    return Item(title=title, url="https://e/x", source="src", category="ai", **kw)


def _ranked() -> dict[str, list[Item]]:
    item = _item("Big <AI> News", summary="A thing happened.", why="It is relevant.")
    return {"ai": [item], "tech": []}


def _cfg() -> AppConfig:
    return AppConfig(
        recipient_email="me@example.com",
        top_n_per_category=5,
        categories={"ai": []},
    )


def test_render_subject_format() -> None:
    assert render_subject(_NOW) == "News digest — Jun 15, 2026"


def test_render_html_includes_content_and_escapes() -> None:
    html = render_html(_ranked(), _NOW)
    assert "A thing happened." in html
    assert "Why it matters:" in html
    assert 'href="https://e/x"' in html
    # Title with angle brackets must be HTML-escaped, not raw.
    assert "Big &lt;AI&gt; News" in html
    assert "<AI>" not in html


def test_render_html_skips_empty_category() -> None:
    html = render_html(_ranked(), _NOW)
    # 'ai' has an item and renders; empty 'tech' must not produce a heading.
    assert ">AI<" in html or "AI" in html
    assert "Tech" not in html


def test_render_text_has_items_and_urls() -> None:
    text = render_text(_ranked(), _NOW)
    assert "Big <AI> News" in text  # plain text is not escaped
    assert "https://e/x" in text
    assert "Why it matters: It is relevant." in text


def test_deliver_raises_without_credentials() -> None:
    settings = Settings(smtp_user="", smtp_pass="")
    with pytest.raises(ValueError, match="missing SMTP creds"):
        deliver(_cfg(), settings, _ranked(), now=_NOW)


def test_deliver_sends_with_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_send(**kwargs: Any) -> None:
        captured.update(kwargs)

    monkeypatch.setattr("news_agent.delivery.service.send_email", fake_send)
    settings = Settings(smtp_user="me@gmail.com", smtp_pass="abcd efgh ijkl mnop")
    deliver(_cfg(), settings, _ranked(), now=_NOW)

    assert captured["recipient"] == "me@example.com"
    assert captured["subject"] == "News digest — Jun 15, 2026"
    # App-password spaces are stripped before login.
    assert captured["password"] == "abcdefghijklmnop"
