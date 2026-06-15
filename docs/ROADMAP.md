# Roadmap / future work

Potential improvements gathered while building. Nothing here is urgent — the
agent is shipped and running daily. Revisit after a few days of live digests
(testing period started **2026-06-15**) to decide what's worth doing.

## Candidate updates

- [ ] **Retry-with-backoff for transient fetch errors.** Sources intermittently
  return `403`/`429`/`5xx`, especially from GitHub Actions' shared IPs (seen:
  Import AI `403`, The Batch `429`). Defensive skipping already prevents crashes,
  but a couple of retries with backoff would recover more sources per run and
  improve CI completeness.

- [ ] **Cross-source clustering (iteration 2).** When the same story appears in
  multiple feeds, that agreement is the strongest "hot" signal. Embed titles,
  merge above a similarity threshold, boost the merged item by source count.
  `dedupe()` in `rank.py` is the seam — right location and signature
  (`list[Item] -> list[Item]`, pure) — but it is **not a pure drop-in**. Three
  things the upgrade must address:
  1. **Clustering is a fold, not a filter.** Today's `dedupe` *selects* an
     existing item (keep-max). Clustering *synthesizes* a representative from
     several items. A filter can't always be refactored into a fold without
     touching the call site — this is the crux, not an ordering nit.
  2. **Score must run after the merge** (or as a post-merge boost pass).
     `rank_items` currently does `score → dedupe → sort`; boost-by-source-count
     needs the source count to exist before scoring, so reorder to
     `cluster → score(with cluster_size) → sort`.
  3. **`Item` must carry source multiplicity.** Today an item has a single
     `source`; a merged representative needs to express "how many / which
     sources agreed" (e.g. a `sources` list, length 1 for un-merged items).
  Note (judgment call): #3 — the *representation* of source multiplicity — is
  the one piece that's safe to add ahead of time without guessing the
  merge/boost math (#1, #2 stay correctly unbuilt). Deferred here on strict
  YAGNI, since `source` is read in three places (diversity cap, rendering,
  fetch table), so it's a small-but-real change, not literally ripple-free.
  Blast radius when done: `rank.py` + `models.py` only.

- [ ] **Per-category relevance filter.** Off-topic items leak in because category
  is decided by source, not content (see
  [ADR 0002](decisions/0002-source-based-categorization.md)). Optional
  `include_keywords` per category in `config.yaml` is the likely fix.

- [ ] **Harden LLM JSON output** (see
  [ADR 0001](decisions/0001-llm-output-format.md) future work): strict JSON
  Schema on the OpenAI-compatible path; tool-calling for the Anthropic path to
  guarantee keys/types there too.

- [ ] **The Batch feed reliability.** The kill-the-newsletter bridge is
  rate-limited (`429`-prone). Find a steadier source or lean on retry + cache.

- [ ] **Winter cron.** `0 6 * * *` is 07:00 BST but 06:00 GMT in winter (GitHub
  cron ignores DST). Decide whether to flip to `0 7 * * *` in winter or leave it.

- [ ] **Evaluate summary quality / tune the prompt** after observing a few real
  digests.

- [ ] **Backfill ADRs** for earlier decisions worth recording: Groq as default
  provider, `src/` package layout, the ranking diversity cap + HN squash, the
  per-source RSS item cap.
