# 0002. Source-based categorization (accept off-topic leakage)

- Status: Accepted
- Date: 2026-06-15

## Context

An item's category is the category of the **source** it came from
(`config.yaml` groups sources under `ai` / `tech` / `crypto`). A story is never
re-classified by its actual content.

This means a source that occasionally publishes off-topic stories leaks them
into its category. Observed in a real digest:

- *"Ark Invest bought $500M of SpaceX shares"* — a markets story from CoinDesk,
  shown under **crypto**.
- *"Reve 2.0 Review: best AI image generator"* — an AI story from Decrypt,
  shown under **crypto**.

Crypto/finance/AI outlets cover each other's territory constantly, so this is
expected, not a bug in ranking. Ranking only orders items *within* whatever
bucket categorization assigned.

## Decision

**Keep source-based categorization as-is and document the limitation.** No
content-based relevance filtering for now.

Rationale: for a personal daily digest the occasional adjacent story is low
harm (often still interesting), and the alternatives carry real cost/complexity
that isn't justified yet. Curating which sources sit in which category in
`config.yaml` remains the lever — e.g. drop or move a source that drifts too far.

## Consequences

- Simple and fully declarative: category membership is obvious from
  `config.yaml`, with no hidden filtering logic.
- Off-topic items will occasionally appear in a category. Accepted.
- If this becomes annoying, revisit with one of the alternatives below; this
  ADR would be superseded.

## Alternatives considered

- **Per-category keyword filter** — optional `include_keywords` per category;
  an item must match (title/content) to stay. Cheap, deterministic, declarative,
  and would drop both examples above. Rejected for now only to avoid keyword-list
  maintenance and edge-case false negatives; the most likely future upgrade.
- **LLM relevance gate** — have the model judge each candidate's relevance to
  its category before ranking. Robust to phrasing, but it must run over the full
  candidate pool (not the top-N), adding a new, costlier LLM step and requiring
  over-fetching to backfill dropped slots. Too heavy for the current benefit.
