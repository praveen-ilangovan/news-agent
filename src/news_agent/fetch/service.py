"""Orchestration: build fetchers from config and gather items defensively."""

# Local imports
from ..config import AppConfig, HNSource, RSSSource, Source
from ..logger import get_logger
from ..models import Item
from .abstracts import Fetcher
from .hn import HNFetcher
from .rss import RSSFetcher

LOG = get_logger(__name__)


def build_fetcher(source: Source, category: str) -> Fetcher:
    """Construct the right Fetcher for a source's `type`."""
    if isinstance(source, RSSSource):
        return RSSFetcher(source, category)
    if isinstance(source, HNSource):
        return HNFetcher(source, category)
    raise ValueError(f"unknown source type: {source!r}")


def fetch_all(config: AppConfig, categories: list[str] | None = None) -> list[Item]:
    """Fetch every source across the requested categories (all if None).

    A source that raises is logged as a warning and skipped — the run goes on.
    """
    items: list[Item] = []
    for category, sources in config.categories.items():
        if categories is not None and category not in categories:
            continue
        for source in sources:
            fetcher = build_fetcher(source, category)
            try:
                items.extend(fetcher.fetch())
            except Exception as error:
                LOG.warning(
                    "source failed; skipping",
                    source=source.name,
                    category=category,
                    error=str(error),
                )
    LOG.info("fetch complete", total=len(items))
    return items
