# news-agent — Claude Code Guidelines

A daily news digest agent: fetch → rank/dedupe → summarize → email, run on a
GitHub Actions cron. Built stage by stage; confirm each stage works before the
next.

## Architecture

```
cli.py → pipeline.py
  → fetch/   (rss + hn providers behind a Fetcher abstract)   -> list[Item]
  → rank.py  (pure functions over list[Item]: score, dedupe, top-N)
  → summarize/ (LLM providers behind an LLMProvider abstract)
  → email.py (HTML digest via Gmail SMTP_SSL)
```

### Key design rules

- **`Item` (`models.py`) is the common currency** between every stage.
- **Ranking is pure functions over `list[Item]`** — no I/O. This is the seam
  for the planned cross-source clustering iteration (embed titles, merge above
  a similarity threshold, boost by source count). Keep it structured for that.
- **Fetching is defensive**: a broken/dead source is logged as a warning and
  skipped — never crash the run.
- **Secrets only from env** (never `config.yaml`, never hardcoded). The LLM key
  is read by the name in `config.yaml`'s `llm.api_key_env`.
- **LLM is provider-abstracted**: `AnthropicProvider` + `OpenAICompatibleProvider`
  (Groq/Gemini/OpenRouter/Ollama via base_url+model+api_key_env). Default: Groq.

## Conventions (mirrors recs-app/apps/backend)

- Poetry, `src/news_agent/` layout, Python 3.12.
- **structlog** logging: `LOG = get_logger(__name__)`, `LOG.child("ctx")`. No prints.
- **pydantic-settings** for env secrets; `pydantic` models for `config.yaml`.
- **Typer** CLI.
- Import groups with comment labels: `# Builtin imports`, `# Project specific imports`, `# Local imports`.
- Tests in `tests/unit` (fast, mocked) and `tests/integration` (network/API).

## Commands

```bash
make install    # poetry install + pre-commit install
make check      # poetry check --lock + ruff + mypy
make unittest   # pytest tests/unit
make run        # run the pipeline once
```

Pre-commit (ruff + mypy) runs on commit. Fix failures — do not `--no-verify`.

## Design decisions

Record notable decisions (and their rationale) as numbered ADRs in
`docs/decisions/`. See its `README.md` for the format. Add a new ADR rather
than rewriting an old one when a decision changes.

## Gotchas

- Gmail SMTP needs an **app password**, not the account password.
- Feeds have malformed/missing dates and dead URLs — parse defensively.
- GitHub scheduled crons can fire 10–30 min late; fine for a morning brief.
