"""Orchestration: build a provider from config and summarize ranked items."""

# Local imports
from ..config import LLMConfig, get_env
from ..logger import get_logger
from ..models import Item
from .abstracts import LLMProvider
from .anthropic_provider import AnthropicProvider
from .openai_compatible import OpenAICompatibleProvider
from .parser import parse_summaries
from .prompt import build_prompt

LOG = get_logger(__name__)


def build_provider(config: LLMConfig) -> LLMProvider:
    """Construct the configured LLM provider, reading its API key from env."""
    api_key = get_env(config.api_key_env)
    if not api_key:
        raise ValueError(
            f"missing API key: set {config.api_key_env} (env or .env file)"
        )
    if config.provider == "anthropic":
        return AnthropicProvider(config.model, api_key)
    return OpenAICompatibleProvider(config.model, api_key, config.base_url)


def apply_summaries(items: list[Item], results: list[dict[str, object]]) -> int:
    """Match LLM results back onto items by url; return how many matched."""
    by_url = {r.get("url"): r for r in results if r.get("url")}
    matched = 0
    for item in items:
        result = by_url.get(item.url)
        if result is None:
            continue
        summary = str(result.get("summary") or "").strip()
        why = str(result.get("why") or "").strip()
        item.summary = summary or None
        item.why = why or None
        matched += 1
    return matched


def summarize_ranked(
    provider: LLMProvider, ranked: dict[str, list[Item]]
) -> dict[str, list[Item]]:
    """Summarize each category in one LLM call. A failing category is left
    unsummarized (logged) rather than crashing the whole run."""
    log = LOG.child("summarize")
    for category, items in ranked.items():
        if not items:
            continue
        try:
            raw = provider.complete(build_prompt(category, items))
            matched = apply_summaries(items, parse_summaries(raw))
            log.info("summarized", category=category, items=len(items), matched=matched)
        except Exception as error:
            log.warning(
                "summarize failed; leaving unsummarized",
                category=category,
                error=str(error),
            )
    return ranked
