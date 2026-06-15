# news-agent

A daily news digest agent. Every morning it fetches the latest stories across
configurable categories (AI, tech, crypto to start), ranks them by "hotness,"
summarizes the top N per category with an LLM, and emails a formatted digest.

It runs for free on GitHub Actions (scheduled cron) and delivers via Gmail SMTP.

```
cron trigger → fetch sources → dedupe/rank → summarize → email
```

## Quickstart

```bash
make install      # poetry install + pre-commit hooks
make run          # run the pipeline once (reads config.yaml)
make check        # ruff lint + format + mypy
make unittest     # pytest
```

## Configuration

Everything user-facing lives in [`config.yaml`](./config.yaml): categories,
sources, ranking knobs, recipient, and the LLM provider/model. Adding a source
is a one-line edit; adding a category is one block.

### Sources

| type  | fields | notes |
|-------|--------|-------|
| `rss` | `url`  | Generic RSS/Atom via feedparser. No engagement data → ranked on recency. |
| `hn`  | `query` (optional) | Hacker News via the Algolia API. Provides `points` → real hotness. |

### LLM provider

Summarization is provider-abstracted. The default is **Groq** (free tier) via
the OpenAI-compatible endpoint; switch to Anthropic, Gemini, OpenRouter, etc.
by editing the `llm:` block — no code change required.

```yaml
llm:
  provider: openai_compatible          # or: anthropic
  model: llama-3.3-70b-versatile
  base_url: https://api.groq.com/openai/v1
  api_key_env: GROQ_API_KEY            # which env var holds the key
```

## Design decisions

Notable decisions and their rationale are recorded as ADRs in
[`docs/decisions/`](./docs/decisions/) — e.g. why summarization uses JSON via
constrained decoding ([0001](./docs/decisions/0001-llm-output-format.md)).

## Secrets

Never committed. Provided via environment variables (GitHub Actions secrets in
CI, a local `.env` for development):

| Variable | Purpose |
|----------|---------|
| `GROQ_API_KEY` (or whatever `llm.api_key_env` names) | LLM API key |
| `SMTP_USER` | Gmail address |
| `SMTP_PASS` | Gmail **app password** (not the account password) |

## Deployment (GitHub Actions)

`.github/workflows/daily.yml` runs the pipeline on a schedule:

- `cron: "0 6 * * *"` → 06:00 UTC = **07:00 BST** (07:00 → 06:00 local in GMT
  winter, since GitHub cron is fixed UTC and ignores DST). Scheduled runs may be
  delayed 10–30 min.
- `workflow_dispatch` lets you trigger a run manually from the Actions tab.

Add the three secrets under **Settings → Secrets and variables → Actions**:
`GROQ_API_KEY`, `SMTP_USER`, `SMTP_PASS`.
