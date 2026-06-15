# Builtin imports
from typing import Any

# Project specific imports
import pytest

# Local imports
from news_agent.config import HNSource, RSSSource
from news_agent.fetch.hn import HNFetcher
from news_agent.fetch.rss import RSSFetcher


class _FakeResponse:
    def __init__(self, content: bytes = b"", json_data: Any = None) -> None:
        self.content = content
        self._json = json_data

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        return self._json


_SAMPLE_RSS = b"""<?xml version="1.0"?>
<rss version="2.0"><channel><title>Test</title>
<item><title>Hello World</title><link>https://example.com/a</link>
<pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate></item>
<item><title>No Link Item</title></item>
</channel></rss>"""


def test_rss_fetch_parses_items(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, **kwargs: Any) -> _FakeResponse:
        return _FakeResponse(content=_SAMPLE_RSS)

    monkeypatch.setattr("news_agent.fetch.rss.httpx.get", fake_get)
    source = RSSSource(type="rss", name="Test", url="https://example.com/feed")
    items = RSSFetcher(source, "tech").fetch()

    assert len(items) == 1  # the item without a link is skipped
    item = items[0]
    assert item.title == "Hello World"
    assert item.url == "https://example.com/a"
    assert item.category == "tech"
    assert item.points is None
    assert item.published_at is not None
    assert item.published_at.year == 2024


def test_hn_fetch_parses_hits(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "hits": [
            {
                "title": "Big AI News",
                "url": "https://example.com/ai",
                "objectID": "123",
                "points": 250,
                "created_at_i": 1704110400,
            },
            {
                "title": "Ask HN: something",
                "url": None,
                "objectID": "456",
                "points": 10,
                "created_at_i": 1704110400,
            },
            {"objectID": "789"},  # no title -> skipped
        ]
    }

    def fake_get(url: str, **kwargs: Any) -> _FakeResponse:
        return _FakeResponse(json_data=payload)

    monkeypatch.setattr("news_agent.fetch.hn.httpx.get", fake_get)
    source = HNSource(type="hn", name="HN", query="AI")
    items = HNFetcher(source, "ai").fetch()

    assert len(items) == 2  # the hit without a title is skipped
    assert items[0].points == 250
    # Ask HN style with no url falls back to the HN thread permalink.
    assert items[1].url == "https://news.ycombinator.com/item?id=456"
