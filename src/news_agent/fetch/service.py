"""Orchestration: build fetchers from config and gather items defensively."""

# Local imports
from ..config import AppConfig, HNSource, RSSSource, Source
from ..logger import get_logger
from ..models import Item
from .abstracts import Fetcher
from .cache import DEFAULT_TTL_MINUTES, read_cached_items, write_cached_items
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


def fetch_all(
    config: AppConfig,
    categories: list[str] | None = None,
    *,
    cache: bool = False,
    force: bool = False,
    cache_ttl_minutes: float = DEFAULT_TTL_MINUTES,
) -> list[Item]:
    """Fetch every source across the requested categories (all if None).

    A source that raises is logged as a warning and skipped — the run goes on.

    With ``cache=True``, a fresh on-disk cache is reused (filtered to
    ``categories``) unless ``force=True``. Only full fetches are written back.
    """
    if cache and not force:
        cached = read_cached_items(cache_ttl_minutes)
        if cached is not None:
            items = (
                cached
                if categories is None
                else [item for item in cached if item.category in categories]
            )
            LOG.info("fetch from cache", total=len(items))
            return items

    items = _fetch_live(config, categories)
    if cache and categories is None:
        write_cached_items(items)
    return items


def _fetch_live(config: AppConfig, categories: list[str] | None) -> list[Item]:
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
