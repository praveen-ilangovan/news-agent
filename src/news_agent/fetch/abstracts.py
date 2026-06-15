"""Fetcher abstraction — one concrete implementation per source `type`."""

# Builtin imports
from abc import ABC, abstractmethod

# Local imports
from ..models import Item


class Fetcher(ABC):
    """Fetches stories from a single configured source into normalized Items.

    `fetch()` may raise on failure (dead URL, malformed feed, HTTP error);
    the orchestrator (`fetch_all`) catches and skips broken sources so one
    bad source never crashes the run.
    """

    @abstractmethod
    def fetch(self) -> list[Item]:
        raise NotImplementedError
