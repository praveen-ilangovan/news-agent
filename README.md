# news-agent

A daily news digest agent. Every morning it fetches the latest stories across
configurable categories (AI, tech, crypto to start), ranks them by "hotness,"
summarizes the top N per category with an LLM, and emails you a formatted digest.

It runs **for free** on GitHub Actions (scheduled cron) and delivers via Gmail.

```
cron trigger → fetch sources → dedupe / rank → summarize → email
```

- **Config-driven** — categories, sources, ranking and the LLM provider all live
  in [`config.yaml`](./config.yaml). Adding a source is a one-line edit.
- **Two source types** — generic RSS/Atom feeds and Hacker News (via the Algolia
  API, which gives real engagement `points`).
- **Provider-abstracted LLM** — defaults to **Groq** (free tier); switch to
  Anthropic / Gemini / OpenRouter / Ollama by editing config, no code change.
- **Defensive** — a dead/rate-limited source is logged and skipped, never crashes
  the run.

---

## Prerequisites

- **Python 3.12** (the repo pins `3.12.12` in `.python-version`).
- **[Poetry](https://python-poetry.org/docs/#installation)** for dependencies.
- A **Groq API key** — free at [console.groq.com/keys](https://console.groq.com/keys).
- A **Gmail account** with an **App Password** (requires 2-Step Verification):
  [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
  This is a 16-char, revocable password — *not* your account password.

---

## Getting started (local)

```bash
# 1. Install dependencies + git hooks
make install

# 2. Create your local secrets file and fill it in
cp .env.example .env
#    GROQ_API_KEY=...        (from console.groq.com/keys)
#    SMTP_USER=you@gmail.com
#    SMTP_PASS=<16-char Gmail app password>

# 3. Set who receives the digest
#    edit config.yaml -> recipient_email

# 4. Preview the digest WITHOUT sending (writes digest.html, opens nothing).
#    Needs GROQ_API_KEY (it summarizes); does NOT need SMTP.
make preview && open digest.html      # 'open' is macOS; use your browser elsewhere

# 5. Send it for real (needs SMTP creds)
make run
```

---

## Commands

All commands are also exposed as `poetry run news-agent <cmd>`.

| Make | What it does |
|------|--------------|
| `make install` | `poetry install` + install pre-commit hooks |
| `make check` | Lock check + ruff (lint/format) + mypy (strict) |
| `make unittest` | Run unit tests |
| `make test-integration` | Run live network tests (hits real feeds/APIs) |
| `make fetch` | Fetch all sources and print them (no ranking) |
| `make rank` | Fetch + rank + print the top-N per category |
| `make summarize` | Fetch + rank + LLM-summarize + print |
| `make preview` | Full pipeline, render to `digest.html` (no email) |
| `make run` | Full pipeline and **email** the digest |

Useful flags on the CLI commands:

- `--category ai` — limit to one category (on `fetch` / `rank` / `summarize`).
- `--cache` / `--no-cache` — use the on-disk fetch cache. `fetch`/`rank`/
  `summarize` default to **on** (fast local iteration, avoids re-hitting every
  source); `run` defaults to **off** (always fresh).
- `--force` — bypass and refresh the cache.
- `--dry-run` (on `run`) — render `digest.html` instead of emailing.

---

## Configuration

Everything user-facing lives in [`config.yaml`](./config.yaml).

### Sources

Each source has a `type` and its fields. Adding one is a single list entry;
adding a category is one new block.

| type  | fields | notes |
|-------|--------|-------|
| `rss` | `url`  | Generic RSS/Atom via feedparser. No engagement data → ranked on recency. |
| `hn`  | `query` (optional) | Hacker News via the Algolia API. Provides `points` → real hotness. |

```yaml
categories:
  ai:
    - type: rss
      name: "Simon Willison"
      url: "https://simonwillison.net/atom/everything/"
    - type: hn
      name: "Hacker News (AI/LLM)"
      query: "AI OR LLM"
```

### Ranking knobs

```yaml
top_n_per_category: 5
ranking:
  recency_half_life_hours: 18   # RSS score halves every N hours
  hn_hotness_midpoint: 0.3      # lower => HN points compete harder vs fresh RSS
  max_per_source: 2             # no single feed can monopolize a category
```

HN items are scored with the hotness formula `(points-1)/(age_hours+2)^1.8`,
squashed into `[0,1)`; RSS items use recency decay. Both are normalized so the
two source types are comparable in the per-category top-N.

### LLM provider

```yaml
llm:
  provider: openai_compatible          # or: anthropic
  model: llama-3.3-70b-versatile
  base_url: https://api.groq.com/openai/v1
  api_key_env: GROQ_API_KEY            # which env var holds the key
```

`openai_compatible` works with Groq, OpenRouter, Gemini, Cerebras, Together and
local Ollama — just change `base_url`, `model` and `api_key_env`.

---

## Secrets

Never committed. Provided via environment variables (a local `.env` for
development, GitHub Actions secrets in CI):

| Variable | Purpose |
|----------|---------|
| `GROQ_API_KEY` (or whatever `llm.api_key_env` names) | LLM API key |
| `SMTP_USER` | Gmail address |
| `SMTP_PASS` | Gmail **app password** (not the account password) |

---

## Deployment (GitHub Actions)

To run it yourself: **fork the repo**, then:

1. Add the three secrets under **Settings → Secrets and variables → Actions**:
   `GROQ_API_KEY`, `SMTP_USER`, `SMTP_PASS`.
2. Enable Actions for the fork (the Actions tab).
3. Set `recipient_email` in `config.yaml` (and tweak sources to taste).

[`.github/workflows/daily.yml`](./.github/workflows/daily.yml) then runs it:

- `cron: "17 6 * * *"` → 06:17 UTC = **07:17 BST**. The `:17` minute is
  intentional — top-of-hour crons are congested and often delayed/dropped on
  GitHub, so an off-peak minute is more reliable. GitHub cron is fixed UTC and
  ignores DST, so in GMT winter it fires at 06:17 local; bump the hour for a
  strict ~7am in winter. Scheduled runs may still be delayed; the first
  scheduled run after adding a workflow is also commonly skipped.
- `workflow_dispatch` lets you trigger a run manually from the Actions tab to
  test end-to-end.

---

## Project layout

```
src/news_agent/
├── config.py        # AppConfig (config.yaml) + Settings (env secrets)
├── models.py        # Item — the shared currency across stages
├── fetch/           # RSS + HN fetchers, orchestrator, on-disk cache
├── rank.py          # pure scoring + dedupe (clustering seam)
├── summarize/       # LLMProvider abstract + Groq/Anthropic + JSON parser
├── delivery/        # HTML/text render + Gmail SMTP sender
└── cli.py           # Typer CLI
docs/decisions/      # Architecture Decision Records (ADRs)
docs/ROADMAP.md      # planned / candidate improvements
```

## Docs

- **Design decisions** — [`docs/decisions/`](./docs/decisions/) (why JSON via
  constrained decoding, source-based categorization, ...).
- **Roadmap / future work** — [`docs/ROADMAP.md`](./docs/ROADMAP.md).
