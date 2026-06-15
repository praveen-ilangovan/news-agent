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
  merge above a similarity threshold, boost the merged item by source count. The
  `dedupe()` function in `rank.py` is the seam this slots into.

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
