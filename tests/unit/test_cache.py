# Builtin imports
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Project specific imports
import pytest

# Local imports
from news_agent.fetch import cache as cache_mod
from news_agent.fetch.cache import read_cached_items, write_cached_items
from news_agent.models import Item


@pytest.fixture(autouse=True)
def _tmp_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cache_mod, "CACHE_PATH", tmp_path / "fetch.json")


def _items() -> list[Item]:
    return [
        Item(
            title="A",
            url="https://e/a",
            source="s",
            category="ai",
            published_at=datetime(2026, 1, 1, tzinfo=UTC),
            points=42,
        )
    ]


def test_read_returns_none_when_absent() -> None:
    assert read_cached_items() is None


def test_write_then_read_roundtrips() -> None:
    write_cached_items(_items())
    cached = read_cached_items()
    assert cached is not None
    assert cached[0].title == "A"
    assert cached[0].points == 42
    assert cached[0].published_at == datetime(2026, 1, 1, tzinfo=UTC)


def test_stale_cache_returns_none() -> None:
    write_cached_items(_items())
    # A zero-minute TTL makes any cache immediately stale.
    assert read_cached_items(ttl_minutes=0) is None


def test_unreadable_cache_returns_none() -> None:
    cache_mod.CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    cache_mod.CACHE_PATH.write_text("not json {{{")
    assert read_cached_items() is None
