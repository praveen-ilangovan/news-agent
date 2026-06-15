"""Ranking + dedupe — pure functions over `list[Item]` (no I/O).

This is the seam for the planned cross-source clustering iteration: `dedupe`
currently collapses exact (normalized) title matches; clustering will later
merge near-duplicate titles across sources and boost the merged item by the
number of agreeing sources. Keeping this module pure lets that slot in cleanly.
"""

# Builtin imports
import re
from collections import defaultdict
from datetime import UTC, datetime

# Local imports
from .config import AppConfig, RankingConfig
from .models import Item

# Undated RSS items are treated as moderately old so they don't top the list.
_DEFAULT_AGE_HOURS = 48.0


def normalize_title(title: str) -> str:
    """Lowercase, drop punctuation, collapse whitespace — for dedupe keys."""
    text = re.sub(r"[^\w\s]", " ", title.lower())
    return re.sub(r"\s+", " ", text).strip()


def _age_hours(published_at: datetime | None, now: datetime) -> float:
    if published_at is None:
        return _DEFAULT_AGE_HOURS
    return max(0.0, (now - published_at).total_seconds() / 3600)


def hn_hotness(points: int, age_hours: float) -> float:
    """Hacker News hotness. Clamped at 0 so 0-point stories don't go negative."""
    return float(max(0.0, (points - 1) / (age_hours + 2) ** 1.8))


def recency_score(age_hours: float, half_life_hours: float) -> float:
    """Exponential recency decay in (0, 1]: 1.0 now, 0.5 at one half-life."""
    return float(0.5 ** (age_hours / half_life_hours))


def score_item(item: Item, ranking: RankingConfig, now: datetime) -> float:
    """Normalized score in [0, 1], comparable across source types.

    HN items use the hotness formula squashed into [0, 1) via a saturating
    transform; RSS items (no engagement data) use recency decay alone.
    """
    age = _age_hours(item.published_at, now)
    if item.points is not None:
        hotness = hn_hotness(item.points, age)
        return hotness / (hotness + ranking.hn_hotness_midpoint)
    return recency_score(age, ranking.recency_half_life_hours)


def dedupe(items: list[Item]) -> list[Item]:
    """Collapse items sharing a normalized title, keeping the highest score.

    Clustering seam: a future version merges near-duplicate titles across
    sources and boosts by source count rather than simply dropping duplicates.
    """
    best: dict[str, Item] = {}
    for item in items:
        key = normalize_title(item.title)
        if not key:
            continue
        current = best.get(key)
        if current is None or item.score > current.score:
            best[key] = item
    return list(best.values())


def _take_top_n(items: list[Item], top_n: int, max_per_source: int) -> list[Item]:
    """Take the top-N, allowing at most `max_per_source` items per source.

    `items` must already be sorted by score descending. If the diversity cap
    leaves fewer than `top_n`, backfill from the remaining highest-scored items.
    """
    chosen: list[Item] = []
    per_source: dict[str, int] = defaultdict(int)
    overflow: list[Item] = []
    for item in items:
        if per_source[item.source] < max_per_source:
            chosen.append(item)
            per_source[item.source] += 1
        else:
            overflow.append(item)
    chosen.extend(overflow)  # backfill capped-out items, still score-ordered
    # Selection respects the diversity cap; display order is purely by score.
    return sorted(chosen[:top_n], key=lambda i: i.score, reverse=True)


def rank_items(
    config: AppConfig, items: list[Item], now: datetime | None = None
) -> dict[str, list[Item]]:
    """Score, dedupe and take the top-N per category (config order preserved)."""
    moment = now if now is not None else datetime.now(UTC)

    by_category: dict[str, list[Item]] = defaultdict(list)
    for item in items:
        by_category[item.category].append(item)

    ranking = config.ranking
    ranked: dict[str, list[Item]] = {}
    for category in config.categories:
        bucket = by_category.get(category, [])
        for item in bucket:
            item.score = score_item(item, ranking, moment)
        unique = dedupe(bucket)
        unique.sort(key=lambda i: i.score, reverse=True)
        ranked[category] = _take_top_n(
            unique, config.top_n_per_category, ranking.max_per_source
        )
    return ranked
