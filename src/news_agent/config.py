"""Configuration: user-editable `config.yaml` plus env-based secrets.

- `AppConfig` mirrors `config.yaml` (sources, categories, ranking, llm).
- `Settings` reads secrets from the environment (SMTP creds, etc.).
- LLM API keys are looked up by name (`llm.api_key_env`) via `get_env`, so
  switching providers never requires a code change.
"""

# Builtin imports
import os
from pathlib import Path
from typing import Annotated, Literal

# Project specific imports
import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RankingConfig(BaseModel):
    # RSS recency decay: score halves every `recency_half_life_hours`.
    recency_half_life_hours: float = 18.0
    # HN hotness is squashed to [0, 1) via h / (h + midpoint); this is the
    # hotness value that maps to 0.5, controlling HN-vs-RSS balance in top-N.
    # Lower => engaged HN stories compete harder against fresh RSS items.
    hn_hotness_midpoint: float = 0.3
    # Diversity cap: at most this many items per source in a category's top-N,
    # so one prolific feed can't monopolize the digest. Backfilled if needed.
    max_per_source: int = 2


class LLMConfig(BaseModel):
    provider: Literal["anthropic", "openai_compatible"] = "openai_compatible"
    model: str = "llama-3.3-70b-versatile"
    base_url: str | None = None
    api_key_env: str = "GROQ_API_KEY"


class RSSSource(BaseModel):
    type: Literal["rss"]
    name: str
    url: str


class HNSource(BaseModel):
    type: Literal["hn"]
    name: str
    query: str = ""


Source = Annotated[RSSSource | HNSource, Field(discriminator="type")]


class AppConfig(BaseModel):
    recipient_email: str
    top_n_per_category: int = 5
    ranking: RankingConfig = RankingConfig()
    llm: LLMConfig = LLMConfig()
    categories: dict[str, list[Source]]


class Settings(BaseSettings):
    """Secrets / environment. Loaded from real env vars or a local `.env`."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    smtp_user: str | None = None
    smtp_pass: str | None = None


def load_config(path: Path | str = "config.yaml") -> AppConfig:
    raw = yaml.safe_load(Path(path).read_text())
    return AppConfig.model_validate(raw)


def get_env(name: str) -> str | None:
    """Read a named environment variable (used for the configured LLM API key)."""
    return os.environ.get(name)
