"""Summarization: provider-abstracted LLM layer.

Public surface: `build_provider` (factory) and `summarize_ranked` (orchestrator).
"""

# Local imports
from .abstracts import LLMProvider
from .service import build_provider, summarize_ranked

__all__ = ["LLMProvider", "build_provider", "summarize_ranked"]
