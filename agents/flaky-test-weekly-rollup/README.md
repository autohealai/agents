# Flaky Test Weekly Rollup

A once-a-week **CI-reliability summary** for your GitHub Actions pipeline. It posts a single Slack
message with the headline numbers — flaky rate, week-over-week trend, how much CI time reruns wasted,
and how the flaky backlog is being worked down. It is **read-only**: it never opens issues, merges, or
changes CI. The only thing it writes is the one Slack summary.

This is the trend companion to the daily [`flaky-test-detective`](../flaky-test-detective/): the
detective finds and files individual flakes each day; the rollup steps back once a week and answers
"is CI getting more or less reliable, and are we keeping up with the backlog?"

## What it does
1. Runs on a schedule (weekly) — no input to type.
2. Scans two windows — the **last 7 days** and the **7 days before that** — over the same merge
   pipeline the detective uses: PR checks (`pull_request`) plus post-merge `push` on the mainline.
   Scheduled/automation workflows are excluded (they re-run on the same commit and would masquerade
   as flakes).
3. Computes, per window: total runs, flaky runs (same-commit flips + rerun-recoveries), flaky rate,
   reruns triggered, and estimated CI-minutes wasted.
4. Reads the flaky backlog from the detective's issue label: how many are open, how many opened this
   week, how many were closed this week, and the age of the oldest open one.
5. Posts one Slack summary with the week-over-week deltas (▲ worse / ▼ better), a link to the label
   board, and a link to the top offender's recent runs. Posts an all-clear when the week was clean.

## Use it
1. Copy `agent.yaml` into a new agent in Autoheal.
2. Edit the block at the top of the instructions: set `REPO`, `BRANCH`, `SLACK_CHANNEL`, and `LABEL`
   (use the **same label** your `flaky-test-detective` files under, default `flaky-test`).
3. Connect the **GitHub** integration (**read** is enough) and the **Slack** integration (**write**).
4. Add a **Schedule** trigger — once a week (e.g. Monday morning) is the intent.
5. Run it once manually and read the Slack summary, then activate the schedule.

## Model
The YAML ships with `gpt-5-mini` at high reasoning effort. The agent is **model-agnostic** — its
instructions use no provider-specific features and it drives the `gh` CLI — so it runs on any approved
LLM out of the box. Swap it in the builder's Budget or edit the `model:` field; `thinking: high` maps
to the provider's reasoning setting automatically.

## Needs
- **GitHub integration** with **read** access — the sandbox injects its credentials so `gh` can read
  Actions runs and list issues. This agent never writes to GitHub.
- **Slack integration** with **write** access — for the weekly summary.
- **GitHub Actions** as your CI, and the `flaky-test-detective` (or any agent) filing issues under a
  shared label so the backlog line has something to report.

## Notes
- **Trend, not detail.** It deliberately posts no run lists and no test names (beyond one optional
  "top recurring" line). For the per-test detail and tracking issues, use the daily
  [`flaky-test-detective`](../flaky-test-detective/).
- **Evidence only.** Flaky rate counts only same-commit-flip and rerun-recovered runs; a run that only
  ever failed is a real failure, not flaky, and is excluded.
- **Estimates are labeled.** Wasted CI-minutes is an approximation from run durations and is worded
  "about N".
- **Pairs with** [`flaky-test-detective`](../flaky-test-detective/) — run both against the same repo
  and label: the detective daily, this rollup weekly.
