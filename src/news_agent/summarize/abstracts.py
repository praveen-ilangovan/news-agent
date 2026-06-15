"""LLMProvider abstraction — one implementation per provider family."""

# Builtin imports
from abc import ABC, abstractmethod

# System prompt shared by all providers: factual, grounded, JSON-only.
SYSTEM_PROMPT = (
    "You are a concise tech-news editor. You write factual two-sentence "
    "summaries and a one-line 'why it matters' for each story. You rely only "
    "on the information provided and never invent facts or URLs. You always "
    "respond with a single JSON array and nothing else."
)


class LLMProvider(ABC):
    """Turns a prompt into completion text. Implementations wrap a vendor SDK."""

    @abstractmethod
    def complete(self, prompt: str) -> str:
        raise NotImplementedError
