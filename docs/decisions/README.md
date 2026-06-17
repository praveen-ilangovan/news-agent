# Architecture Decision Records (ADRs)

This directory records notable design decisions and *why* we made them, so the
reasoning survives even when the code changes.

Each ADR is a numbered, immutable-ish file. If a decision is later reversed,
add a new ADR that supersedes the old one (and mark the old one's status)
rather than deleting history.

## Format

```
# NNNN. Title
- Status: Accepted | Superseded by NNNN | Deprecated
- Date: YYYY-MM-DD
## Context     (the forces/problem)
## Decision    (what we chose)
## Consequences (trade-offs, follow-ups)
## Alternatives considered
```

## Index

| # | Title | Status |
|---|-------|--------|
| [0001](0001-llm-output-format.md) | LLM summarization output format (JSON via constrained decoding) | Accepted |
| [0002](0002-source-based-categorization.md) | Source-based categorization (accept off-topic leakage) | Accepted |
| [0003](0003-external-trigger-over-github-cron.md) | External scheduler over GitHub cron | Accepted |
