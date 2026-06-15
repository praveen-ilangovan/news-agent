"""Hacker News fetcher via the Algolia API — the one source with real points."""

# Builtin imports
import time
from datetime import UTC, datetime

# Project specific imports
import httpx

# Local imports
from ..config import HNSource
from ..logger import get_logger
from ..models import Item
from .abstracts import Fetcher
from .constants import HTTP_TIMEOUT, USER_AGENT

LOG = get_logger(__name__)

_ENDPOINT = "https://hn.algolia.com/api/v1/search"
_HITS_PER_PAGE = 30
# Restrict to recent stories so a popularity search doesn't return all-time hits.
_RECENCY_DAYS = 3


class HNFetcher(Fetcher):
    def __init__(self, source: HNSource, category: str) -> None:
        self._source = source
        self._category = category
        self._log = LOG.child("hn")

    def fetch(self) -> list[Item]:
        cutoff = int(time.time()) - _RECENCY_DAYS * 86400
        params = {
            "tags": "story",
            "hitsPerPage": str(_HITS_PER_PAGE),
            "numericFilters": f"created_at_i>{cutoff}",
        }
        if self._source.query:
            params["query"] = self._source.query

        response = httpx.get(
            _ENDPOINT,
            params=params,
            timeout=HTTP_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        hits = response.json().get("hits", [])

        items: list[Item] = []
        for hit in hits:
            title = hit.get("title")
            object_id = hit.get("objectID")
            if not title or not object_id:
                continue
            # Ask/Show HN and text posts have no external url -> link to the thread.
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
            created = hit.get("created_at_i")
            published_at = datetime.fromtimestamp(created, tz=UTC) if created else None
            items.append(
                Item(
                    title=str(title).strip(),
                    url=str(url),
                    source=self._source.name,
                    category=self._category,
                    published_at=published_at,
                    points=hit.get("points"),
                )
            )
        self._log.info("fetched", source=self._source.name, count=len(items))
        return items
