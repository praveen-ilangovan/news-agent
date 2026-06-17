# 0003. External scheduler over GitHub cron

- Status: Accepted
- Date: 2026-06-17

## Context

The daily digest ran in a GitHub Actions workflow (`daily.yml`) triggered by a
`schedule:` cron. It never delivered on schedule. Investigation showed:

- The workflow was `active`, on the default branch (`main`), with all secrets
  present, and **two manual `workflow_dispatch` runs succeeded end-to-end** —
  so the pipeline, secrets, and config were all correct.
- `gh run list --event schedule` returned **zero runs, ever**, despite two
  scheduled windows fully elapsing (Jun 16 06:00 UTC under `0 6`, Jun 17
  06:17 UTC under `17 6`).

So the trigger — not our setup — was the failure. GitHub's scheduled workflows
are explicitly best-effort: under load they are delayed 10–30 min and, on
low-activity repos or congested minutes, silently dropped. Moving the cron
off-peak (ADR-less commit `aae2659`) reduces but does not remove this; the
schedule is fundamentally unreliable for a "must arrive every morning" job.

## Decision

**Drive the workflow from an external scheduler that POSTs to the
`workflow_dispatch` REST API, and remove GitHub's `schedule:` trigger.**

- GitHub Actions stays the *runner* (free compute, secrets already configured,
  pipeline already proven). Only the *trigger* moves out.
- The external scheduler is an HTTP cron service (cron-job.org), firing one
  authenticated `POST .../workflows/daily.yml/dispatches` per morning with a
  fine-grained PAT scoped to this repo (Actions: read+write).
- `workflow_dispatch` becomes the single entry point — it was already proven
  by the manual runs, and it stays usable for ad-hoc runs from the UI/CLI.

The `schedule:` line is removed rather than kept as a backstop: the digest has
no email idempotency, so a flaky-but-occasional second trigger would risk
double-sends and muddy "why did/didn't it run" debugging. One reliable trigger
beats two unreliable ones.

## Consequences

- A new secret (the PAT) now lives outside GitHub, in cron-job.org. Fine-grained
  PATs expire (max 1 year) → a yearly rotation chore. Track it.
- If cron-job.org fails, there is no in-GitHub fallback. Acceptable: it is a
  purpose-built scheduler, far more reliable than GitHub cron was.
- Trigger reliability is now independent of GitHub Actions scheduler load.

## Alternatives considered

- **Backstop GitHub cron + email idempotency** — keep `schedule:`, add a second
  off-peak cron line, and dedupe so missed/double fires self-heal. Zero new
  infra/secrets, but still leans on the unreliable scheduler and needs new
  idempotency code. Deferred; could layer on later if desired.
- **Cloud scheduler (GCP Cloud Scheduler / AWS EventBridge)** — rock-solid, but
  requires a cloud account and IAM/auth setup. Overkill for a personal digest
  unless already in that ecosystem.
- **Always-on machine crontab** — no always-on box available (primary machine
  is a laptop), so not viable.
- **Claude `/schedule` cloud routine** — spins up a full agent session daily
  just to fire one HTTP call, tied to account/credits. Wrong tool for a fixed
  daily ping.
