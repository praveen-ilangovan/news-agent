"""Anthropic provider — uses the Anthropic SDK with a Claude model."""

# Project specific imports
from anthropic import Anthropic

# Local imports
from .abstracts import SYSTEM_PROMPT, LLMProvider

_MAX_TOKENS = 2048


class AnthropicProvider(LLMProvider):
    def __init__(self, model: str, api_key: str) -> None:
        self._client = Anthropic(api_key=api_key)
        self._model = model

    def complete(self, prompt: str) -> str:
        message = self._client.messages.create(
            model=self._model,
            max_tokens=_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        parts: list[str] = []
        for block in message.content:
            text = getattr(block, "text", None)
            if isinstance(text, str):
                parts.append(text)
        return "".join(parts)
