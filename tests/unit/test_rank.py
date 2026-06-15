# Builtin imports
from datetime import UTC, datetime, timedelta

# Local imports
from news_agent.config import AppConfig, RankingConfig
from news_agent.models import Item
from news_agent.rank import (
    hn_hotness,
    normalize_title,
    rank_items,
    recency_score,
)

_NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _cfg(top_n: int = 3) -> AppConfig:
    return AppConfig(
        recipient_email="x@y.com",
        top_n_per_category=top_n,
        ranking=RankingConfig(),
        categories={"ai": []},
    )


def _item(title: str, points: int | None = None, hours_old: float = 1.0) -> Item:
    return Item(
        title=title,
        url=f"https://example.com/{title}",
        source="hn" if points is not None else "rss",
        category="ai",
        published_at=_NOW - timedelta(hours=hours_old),
        points=points,
    )


def test_normalize_title_strips_punctuation_and_case() -> None:
    assert normalize_title("Hello, World!") == "hello world"
    assert normalize_title("  OpenAI   ships   GPT-9  ") == "openai ships gpt 9"


def test_recency_score_decays_with_age() -> None:
    assert recency_score(0, 18) == 1.0
    assert recency_score(18, 18) == 0.5
    assert recency_score(36, 18) < recency_score(18, 18)


def test_hn_hotness_is_nonnegative_and_rewards_points() -> None:
    assert hn_hotness(0, 5) == 0.0  # clamped, never negative
    assert hn_hotness(500, 5) > hn_hotness(50, 5)


def test_rank_respects_top_n_and_orders_by_score() -> None:
    items = [_item(f"story {i}", hours_old=float(i)) for i in range(6)]
    ranked = rank_items(_cfg(top_n=3), items, now=_NOW)["ai"]
    assert len(ranked) == 3
    scores = [i.score for i in ranked]
    assert scores == sorted(scores, reverse=True)


def test_dedupe_keeps_higher_scoring_duplicate() -> None:
    # Same title from HN (fresh, high points) and RSS (stale) -> HN survives.
    hot = _item("Same Title", points=500, hours_old=2.0)
    cold = _item("same title!", hours_old=200.0)
    ranked = rank_items(_cfg(), [cold, hot], now=_NOW)["ai"]
    assert len(ranked) == 1
    assert ranked[0].source == "hn"


def test_diversity_cap_limits_items_per_source() -> None:
    # Five items from one prolific source; cap is 2, but backfill fills top_n.
    cfg = _cfg(top_n=3)
    cfg.ranking.max_per_source = 2
    prolific = [_item(f"prolific {i}", hours_old=float(i)) for i in range(5)]
    other = _item("from elsewhere", hours_old=1.5)
    other.source = "other"
    ranked = rank_items(cfg, [*prolific, other], now=_NOW)["ai"]
    assert len(ranked) == 3
    # The lone other-source item must earn a slot despite lower-aged rivals.
    assert any(i.source == "other" for i in ranked)


def test_fresh_rss_can_outrank_stale_hn() -> None:
    fresh_rss = _item("Brand New Post", hours_old=1.0)
    stale_hn = _item("Old Discussion", points=20, hours_old=48.0)
    ranked = rank_items(_cfg(), [stale_hn, fresh_rss], now=_NOW)["ai"]
    assert ranked[0].title == "Brand New Post"
