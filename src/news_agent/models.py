"""Core domain models shared across fetch -> rank -> summarize -> email."""

# Builtin imports
from datetime import datetime

# Project specific imports
from pydantic import BaseModel


class Item(BaseModel):
    """A single normalized story, emitted by fetchers and consumed everywhere else.

    Fetchers produce these; ranking operates on `list[Item]` as a pure function
    (the seam where cross-source clustering will later merge items); summarization
    fills in `summary` / `why`.
    """

    title: str
    url: str
    source: str
    category: str
    published_at: datetime | None = None
    # Engagement signal — only Hacker News provides this. None for RSS items.
    points: int | None = None
    # Computed by the ranking step (hotness for HN, recency decay for RSS).
    score: float = 0.0
    # Filled in by the summarization step.
    summary: str | None = None
    why: str | None = None
