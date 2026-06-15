# Project specific imports
from news_agent.config import AppConfig, load_config


def test_seed_config_loads() -> None:
    cfg = load_config("config.yaml")
    assert isinstance(cfg, AppConfig)
    assert cfg.top_n_per_category >= 1
    assert {"ai", "tech", "crypto"} <= set(cfg.categories)
    assert cfg.llm.provider in {"anthropic", "openai_compatible"}


def test_hn_and_rss_sources_parse() -> None:
    cfg = load_config("config.yaml")
    ai_types = {s.type for s in cfg.categories["ai"]}
    assert {"rss", "hn"} <= ai_types
