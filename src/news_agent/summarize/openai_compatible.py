"""OpenAI-compatible provider — works with Groq, OpenRouter, Gemini, Ollama..."""

# Project specific imports
from openai import OpenAI

# Local imports
from .abstracts import SYSTEM_PROMPT, LLMProvider

_MAX_TOKENS = 2048
_TEMPERATURE = 0.2


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, model: str, api_key: str, base_url: str | None) -> None:
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    def complete(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=_MAX_TOKENS,
            temperature=_TEMPERATURE,
            # JSON mode forces syntactically valid JSON (an object), avoiding
            # the unquoted-value failures some models produce in free text.
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content or ""
