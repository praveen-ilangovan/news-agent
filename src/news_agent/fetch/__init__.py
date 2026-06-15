"""Fetching: turn configured sources into normalized `Item`s.

Public surface: `fetch_all` (orchestrator) and `build_fetcher` (factory).
"""

# Local imports
from .service import build_fetcher, fetch_all

__all__ = ["build_fetcher", "fetch_all"]
