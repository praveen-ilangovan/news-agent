"""On-disk cache of fetched items, for fast local iteration.

Stores the full fetch (all categories) as JSON with a timestamp. Intended for
dev/debug commands so repeated runs don't re-hit every source (and trip rate
limits like kill-the-newsletter's 429). The production `run` fetches fresh.
"""

# Builtin imports
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Local imports
from ..logger import get_logger
from ..models import Item

LOG = get_logger(__name__)

CACHE_PATH = Path(".cache/fetch.json")
DEFAULT_TTL_MINUTES = 60.0


def read_cached_items(ttl_minutes: float = DEFAULT_TTL_MINUTES) -> list[Item] | None:
    """Return cached items if a fresh cache exists, else None."""
    if not CACHE_PATH.exists():
        return None
    try:
        payload = json.loads(CACHE_PATH.read_text())
        cached_at = datetime.fromisoformat(payload["cached_at"])
        if datetime.now(UTC) - cached_at > timedelta(minutes=ttl_minutes):
            LOG.info("cache stale; refetching", cached_at=payload["cached_at"])
            return None
        return [Item.model_validate(entry) for entry in payload["items"]]
    except (json.JSONDecodeError, KeyError, ValueError) as error:
        LOG.warning("ignoring unreadable cache", error=str(error))
        return None


def write_cached_items(items: list[Item]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "cached_at": datetime.now(UTC).isoformat(),
        "items": [item.model_dump(mode="json") for item in items],
    }
    CACHE_PATH.write_text(json.dumps(payload, indent=2))
    LOG.info("cache written", path=str(CACHE_PATH), total=len(items))
