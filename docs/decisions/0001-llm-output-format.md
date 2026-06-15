# 0001. LLM summarization output format (JSON via constrained decoding)

- Status: Accepted
- Date: 2026-06-15

## Context

The summarization stage asks an LLM to return structured data for a batch of
stories: a list of `{title, url, summary, why}` objects, one per story.

We initially requested **free-form JSON** in the prompt and parsed it. On the
first live run, `llama-3.3-70b-versatile` (via Groq) returned **syntactically
invalid JSON** — string values were emitted without surrounding quotes:

```
"summary": Julia Evans writes for a specific person...   ← not a JSON string
"why": It matters because...
```

This raised a fair question: *is JSON the right format at all, given it's prone
to syntax errors (unbalanced braces, trailing commas, fences, unquoted values)?*

The key insight: there are two very different ways a model produces JSON.

1. **Free-form** — the model generates text and we hope it's valid JSON. Fragile.
2. **Constrained decoding** (`response_format={"type":"json_object"}`) — the
   inference engine restricts token sampling so only tokens that keep the JSON
   valid can be emitted. Malformed JSON becomes *impossible to produce*, not
   merely discouraged.

The invalid output above came from path (1). Switching to path (2) fixed it.

## Decision

**Keep JSON, but rely on constrained decoding rather than free-form generation,
plus a tolerant parser for defense in depth.**

Concretely:

- The OpenAI-compatible provider (Groq, the default) sets
  `response_format={"type":"json_object"}`, which guarantees syntactically
  valid JSON. JSON mode requires an object, so the prompt asks for
  `{"summaries": [ ... ]}`.
- The parser (`summarize/parser.py`) is defensive: it strips markdown fences,
  accepts both an object-wrapped array and a bare array, digs the array out of
  whatever key the model used, and falls back to scanning for the outermost
  `{...}` / `[...]`.
- Results are matched back to items **by URL**; any item without a match (or a
  missing field) is simply left unsummarized — never a crash.

## Why JSON fits *this* data specifically

- The payload is flat and tiny (≈5 objects × 4 string fields). The classic JSON
  failure modes (deep nesting, arrays of arrays) don't apply.
- JSON **escapes messy summary text for free** — summaries contain quotes,
  colons, em-dashes and occasional newlines. A delimited format is robust to
  *syntax* but breaks when the *content* contains the delimiter; JSON does not.
- With constrained decoding the syntax-error class is eliminated; the only
  residual risk is semantic (a dropped/renamed key), which the URL-matching +
  `None` fallback already tolerate.

## Consequences

- **Default (Groq) path is robust**: syntactically valid JSON is guaranteed.
- **Weak spot — Anthropic path**: Anthropic does not accept `response_format`,
  so on that path we are back to free-form generation + the tolerant parser.
  Acceptable because Anthropic is not the default; flagged for hardening below.
- The parser must stay tolerant of multiple shapes (object-wrapped vs bare
  array) precisely because providers differ. This is intentional, not cruft.

## Alternatives considered

- **Free-form JSON in prose** — rejected; this is the failure we hit.
- **JSON Schema / strict structured outputs** — guarantees keys/types too, not
  just syntax. Deferred: support is model-dependent; revisit if we observe
  semantic drift (would let us drop the URL-matching fallback).
- **Tool/function calling** — gives both Groq *and* Anthropic a key/type
  guarantee. The natural way to close the Anthropic weak spot later.
- **Tagged/delimited text** (e.g. `WHY: ...` per line) — robust to syntax and
  provider-agnostic, but fragile when summary content contains the delimiter,
  and loses JSON's clean escaping. Rejected for this reason.

## Future hardening (not done yet)

- Upgrade the OpenAI-compatible path to strict JSON Schema once the model's
  support is verified.
- Use tool-calling for the Anthropic path to match the Groq guarantee.
