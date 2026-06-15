"""Shared HTTP constants for fetchers."""

USER_AGENT = "news-agent/0.1 (+https://github.com/praveen-ilangovan/news-agent)"
HTTP_TIMEOUT = 15.0
# Cap items kept per source. Some RSS feeds carry years of history (OpenAI ~1000,
# Anthropic ~238); a daily digest only cares about the most recent handful.
MAX_ITEMS_PER_FEED = 30
