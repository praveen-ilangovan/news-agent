"""Defensive parsing of the LLM's JSON response.

Providers differ: OpenAI-compatible JSON mode returns an object like
`{"summaries": [...]}`, while Anthropic returns a bare array (possibly with
fences or prose). We handle both, and dig the array out of whatever object the
model wrapped it in.
"""

# Builtin imports
import json
from typing import Any

# Keys a model might wrap the array under, tried in order before falling back
# to "first list value in the object".
_ARRAY_KEYS = ("summaries", "items", "stories", "results", "data")


def _strip_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # Drop the opening fence (``` or ```json) and the trailing fence.
        cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned
        if cleaned.endswith("```"):
            cleaned = cleaned[: -len("```")]
    return cleaned.strip()


def _extract_list(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [element for element in data if isinstance(element, dict)]
    if isinstance(data, dict):
        for key in _ARRAY_KEYS:
            value = data.get(key)
            if isinstance(value, list):
                return [e for e in value if isinstance(e, dict)]
        for value in data.values():
            if isinstance(value, list):
                return [e for e in value if isinstance(e, dict)]
    raise ValueError("no JSON array of objects found")


def parse_summaries(raw: str) -> list[dict[str, Any]]:
    """Extract the list of summary objects. Raises ValueError if none found."""
    text = _strip_fences(raw)

    # 1) Try parsing the whole response (the common, well-formed case).
    try:
        return _extract_list(json.loads(text))
    except (json.JSONDecodeError, ValueError):
        pass

    # 2) Fall back to the outermost {...} object, then the outermost [...] array.
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start, end = text.find(open_ch), text.rfind(close_ch)
        if start != -1 and end > start:
            try:
                return _extract_list(json.loads(text[start : end + 1]))
            except (json.JSONDecodeError, ValueError):
                continue

    raise ValueError("no JSON found in LLM response")
