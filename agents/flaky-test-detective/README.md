# Flaky Test Detective

Finds **flaky tests** in your GitHub Actions CI — tests that pass and fail with no code change — and
makes them visible and tracked. On each run it files or updates a **tracking issue** per confirmed
flaky test and posts a **scoreboard** to Slack. It only opens/updates issues and posts to Slack — it
never merges, force-pushes, edits code, or disables a test without a tracking issue. A human decides
every fix.

Flakiness is proven from CI history, not guessed: a test is only reported when the **same commit**
both passed and failed, or a **re-run recovered** a failure with no new code. A test that only ever
failed is a real failure, not flaky, and is left alone.

## What it does
1. Runs on a schedule (e.g. nightly) — no input to type.
2. Lists completed CI runs in the last `WINDOW_HOURS`, scoped to the **merge pipeline**: PR checks
   (`pull_request`) plus post-merge `push` on the mainline. Scheduled/automation workflows are
   excluded — they re-run on the same commit and would masquerade as flakes.
3. Confirms flakiness two ways: **same-commit flip** (a workflow that both succeeded and failed on
   one SHA) and **rerun-recovered** (a failed attempt that passed on re-run, no new commit).
4. Extracts the failing **test name** from the logs (Go, pytest, Jest/Vitest, RSpec, JUnit); if a
   workflow has no test name (lint/gate/status jobs), it tracks the flake at **job level**.
5. Files or updates one **tracking issue** per flaky test (deduplicated by a hidden marker, capped
   per run), with occurrence count, suspected cause, evidence links, and an error snippet.
6. Posts one Slack **scoreboard**: how many runs it reviewed (coverage), how many were flaky, and the
   top offenders — each with a clickable issue and logs link. Posts an all-clear when nothing flaked.

## Use it
1. Copy `agent.yaml` into a new agent in Autoheal.
2. Edit the block at the top of the instructions: set `REPO`, `BRANCH`, `SLACK_CHANNEL`, and
   optionally `WINDOW_HOURS`, `LABEL`, `MAX_NEW_ISSUES`.
3. Create the issue label once (default `flaky-test`) in the repo, so issues are grouped.
4. Connect the **GitHub** integration (grant **write** — it opens/updates issues) and the **Slack**
   integration (grant **write** — it posts the scoreboard).
5. Add a **Schedule** trigger — nightly is a good default. Match `WINDOW_HOURS` to the cadence (a
   nightly run wants a 24h window).
6. Run it once manually, read the issues it filed and the Slack scoreboard, then activate the
   schedule.

## Model
The YAML ships with `gpt-5-mini` at high reasoning effort. The agent is **model-agnostic** — its
instructions use no provider-specific features and it drives the `gh` CLI — so it runs on any
approved LLM out of the box. Swap it in the builder's Budget or edit the `model:` field;
`thinking: high` maps to the provider's reasoning setting automatically.

## Needs
- **GitHub integration** with **write** access — the sandbox injects its credentials so `gh` can read
  Actions runs and logs and open/update issues.
- **Slack integration** with **write** access — for the scoreboard message.
- **GitHub Actions** as your CI. The detection reads `repos/.../actions/runs`; other CI systems
  (GitLab CI, CircleCI, Buildkite) are not covered by this agent.

## Notes
- **Evidence only.** It reports a test as flaky solely on same-commit-flip or rerun-recovered
  evidence. Failures that never flipped are treated as real and ignored.
- **Never disables a test.** The most it does is open an issue asking a human to fix or quarantine
  (with a link back). It never edits code, merges, or force-pushes.
- **Job-level fallback.** Workflows without a parseable test name (lint, scope, status gates) are
  still tracked, labeled `job-level (see logs)`, so the flake isn't lost — the logs link shows what
  failed.
- **Test-level detail depends on your logs.** Test names are extracted from CI output. If a job
  hides individual test results (or uploads them only as artifacts), the flake is tracked at job
  level. Emitting standard test output (e.g. JUnit XML) improves per-test attribution.
- **Governance.** If a policy gates every write on human approval, the issue/comment and the Slack
  post pause as "waiting for input" until approved.
- **Pairs with** [`flaky-test-weekly-rollup`](../flaky-test-weekly-rollup/) — the read-only weekly
  trend companion. Run this detective daily and the rollup weekly against the same repo and label.
