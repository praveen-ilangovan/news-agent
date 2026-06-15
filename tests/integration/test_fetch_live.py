"""Live network tests. Run with: make test-integration"""

# Project specific imports
import pytest

# Local imports
from news_agent.config import HNSource, RSSSource
from news_agent.fetch.hn import HNFetcher
from news_agent.fetch.rss import RSSFetcher


@pytest.mark.integration
def test_live_rss_fetch() -> None:
    source = RSSSource(
        type="rss",
        name="Simon Willison",
        url="https://simonwillison.net/atom/everything/",
    )
    items = RSSFetcher(source, "ai").fetch()
    assert len(items) > 0
    assert all(item.title and item.url for item in items)


@pytest.mark.integration
def test_live_hn_fetch() -> None:
    source = HNSource(type="hn", name="HN", query="AI OR LLM")
    items = HNFetcher(source, "ai").fetch()
    assert len(items) > 0
    # HN is the source that gives engagement data.
    assert any(item.points is not None for item in items)
