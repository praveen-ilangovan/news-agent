"""RSS/Atom fetcher via feedparser. No engagement data -> ranked on recency."""

# Builtin imports
import calendar
import html
import re
from datetime import UTC, datetime
from typing import Any

# Project specific imports
import feedparser
import httpx

# Local imports
from ..config import RSSSource
from ..logger import get_logger
from ..models import Item
from .abstracts import Fetcher
from .constants import HTTP_TIMEOUT, MAX_ITEMS_PER_FEED, USER_AGENT

# Sentinel for sorting items that have no parseable date (treated as oldest).
_NO_DATE = datetime.min.replace(tzinfo=UTC)

_TAG_RE = re.compile(r"<[^>]+>")
_CONTENT_LIMIT = 600


def _clean_html(text: str) -> str:
    """Strip tags, unescape entities, collapse whitespace, truncate."""
    stripped = _TAG_RE.sub(" ", text)
    unescaped = html.unescape(stripped)
    collapsed = re.sub(r"\s+", " ", unescaped).strip()
    return collapsed[:_CONTENT_LIMIT]


LOG = get_logger(__name__)


def _parse_struct_time(entry: Any) -> datetime | None:
    """Best-effort parse of a feed entry's date; feeds often omit/mangle it."""
    for key in ("published_parsed", "updated_parsed"):
        value = entry.get(key)
        if value:
            # feedparser normalizes *_parsed to UTC struct_time -> use timegm.
            return datetime.fromtimestamp(calendar.timegm(value), tz=UTC)
    return None


class RSSFetcher(Fetcher):
    def __init__(self, source: RSSSource, category: str) -> None:
        self._source = source
        self._category = category
        self._log = LOG.child("rss")

    def fetch(self) -> list[Item]:
        # Fetch with httpx (timeout + UA) rather than letting feedparser do the
        # network call, so we control timeouts and some feeds don't 403 us.
        response = httpx.get(
            self._source.url,
            timeout=HTTP_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
        if parsed.bozo and not parsed.entries:
            raise ValueError(f"malformed feed: {parsed.bozo_exception!r}")

        items: list[Item] = []
        for entry in parsed.entries:
            title = entry.get("title")
            link = entry.get("link")
            if not title or not link:
                continue
            raw_summary = entry.get("summary") or entry.get("description")
            content = _clean_html(str(raw_summary)) if raw_summary else None
            items.append(
                Item(
                    title=str(title).strip(),
                    url=str(link),
                    source=self._source.name,
                    category=self._category,
                    published_at=_parse_struct_time(entry),
                    content=content or None,
                )
            )
        # Keep only the most recent N; undated items sort last but keep feed order.
        items.sort(key=lambda i: i.published_at or _NO_DATE, reverse=True)
        items = items[:MAX_ITEMS_PER_FEED]
        self._log.info("fetched", source=self._source.name, count=len(items))
        return items
