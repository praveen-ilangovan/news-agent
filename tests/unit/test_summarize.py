# Builtin imports
from datetime import UTC, datetime

# Project specific imports
import pytest

# Local imports
from news_agent.config import LLMConfig
from news_agent.models import Item
from news_agent.summarize.abstracts import LLMProvider
from news_agent.summarize.parser import parse_summaries
from news_agent.summarize.prompt import build_prompt
from news_agent.summarize.service import (
    apply_summaries,
    build_provider,
    summarize_ranked,
)

_NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _item(title: str, url: str) -> Item:
    return Item(title=title, url=url, source="s", category="ai", published_at=_NOW)


class _FakeProvider(LLMProvider):
    def __init__(self, response: str) -> None:
        self._response = response
        self.calls = 0

    def complete(self, prompt: str) -> str:
        self.calls += 1
        return self._response


class _BoomProvider(LLMProvider):
    def complete(self, prompt: str) -> str:
        raise RuntimeError("api down")


def test_parse_strips_fences_and_prose() -> None:
    raw = 'Sure!\n```json\n[{"title": "A", "url": "u", "summary": "s", "why": "w"}]\n```'
    parsed = parse_summaries(raw)
    assert parsed == [{"title": "A", "url": "u", "summary": "s", "why": "w"}]


def test_parse_object_wrapped_array() -> None:
    # JSON mode returns {"summaries": [...]}, not a bare array.
    raw = '{"summaries": [{"url": "u", "summary": "s", "why": "w"}]}'
    assert parse_summaries(raw) == [{"url": "u", "summary": "s", "why": "w"}]


def test_parse_finds_array_under_unknown_key() -> None:
    raw = '{"data_out": [{"url": "u"}]}'
    assert parse_summaries(raw) == [{"url": "u"}]


def test_parse_raises_on_no_array() -> None:
    with pytest.raises(ValueError):
        parse_summaries("I could not produce JSON.")


def test_build_prompt_includes_titles_urls_and_content() -> None:
    item = _item("Big News", "https://e/1")
    item.content = "Some real description text."
    prompt = build_prompt("ai", [item])
    assert "Big News" in prompt
    assert "https://e/1" in prompt
    assert "Some real description text." in prompt


def test_apply_summaries_matches_by_url() -> None:
    items = [_item("A", "https://e/a"), _item("B", "https://e/b")]
    results = [
        {"url": "https://e/a", "summary": "Summ A.", "why": "Matters A."},
        {"url": "https://e/b", "summary": "Summ B.", "why": "Matters B."},
    ]
    matched = apply_summaries(items, results)
    assert matched == 2
    assert items[0].summary == "Summ A."
    assert items[1].why == "Matters B."


def test_summarize_ranked_applies_and_calls_once_per_category() -> None:
    response = (
        '[{"url": "https://e/a", "summary": "S.", "why": "W."}]'
    )
    provider = _FakeProvider(response)
    ranked = {"ai": [_item("A", "https://e/a")], "tech": []}
    out = summarize_ranked(provider, ranked)
    assert provider.calls == 1  # empty 'tech' bucket is skipped
    assert out["ai"][0].summary == "S."


def test_summarize_ranked_survives_provider_error() -> None:
    ranked = {"ai": [_item("A", "https://e/a")]}
    out = summarize_ranked(_BoomProvider(), ranked)
    # No crash; item is simply left unsummarized.
    assert out["ai"][0].summary is None


def test_build_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    cfg = LLMConfig(provider="openai_compatible", api_key_env="GROQ_API_KEY")
    with pytest.raises(ValueError, match="missing API key"):
        build_provider(cfg)


def test_build_provider_selects_openai_compatible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    cfg = LLMConfig(
        provider="openai_compatible",
        model="llama-3.3-70b-versatile",
        base_url="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY",
    )
    provider = build_provider(cfg)
    assert provider.__class__.__name__ == "OpenAICompatibleProvider"
