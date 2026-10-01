# Drata Compliance Reporter

Turns the manual weekly Drata review into a tracked, auditable routine. Once a
week it reads your Drata posture, maintains a rolling GitHub tracker with one
sub-task per failing monitoring test, and posts a single Slack digest. It
**reports and tracks only** — it never changes code, opens a fix PR, or edits
Drata.

## What one run does

1. **Read** — framework **control readiness** (ready controls / total in-scope
   controls, the number on the Drata *Readiness* card) and every failing
   monitoring test with the resources + failed assertions behind it.
2. **Track** — one rolling parent tracker issue for the week (readiness table +
   a `## Sub-tickets` checklist) and one sub-task issue per failing test,
   de-duped against still-open findings so nothing is filed twice.
3. **Report** — one Slack digest: readiness per framework, failing-test totals by
   category, and a link to the tracker.

Every failing test ends the run as a tracked issue — nothing is seen and
dropped.

## Readiness: the number this reports

Control readiness (from `drata-list-controls`, `isReady` per control bucketed by
framework) — the figure on the Drata *Readiness* card. It deliberately does
**not** report the frameworks endpoint's requirement-readiness number; the two
differ, often by 10-20 points, and the card number is the one teams track.

## Configure

Edit the `>>> EDIT THIS BLOCK <<<` section at the top of `agent.yaml`:

| Variable         | What to set                                                     |
| ---------------- | -------------------------------------------------------------- |
| `DRATA_WORKSPACE`| Your Drata workspace id (`1` if you have a single workspace).   |
| `REPO`           | `owner/repo` where the tracker + sub-task issues are filed.     |
| `TRACKER_LABEL`  | Label applied to every issue (create it in the repo first).     |
| `SLACK_CHANNEL`  | Channel for the weekly digest.                                  |

## Integrations required

- **Drata** — read scopes for monitoring tests, controls, and frameworks.
- **GitHub** — connected so the sandbox `gh` CLI can file/read issues in `REPO`.
- **Slack** — a bot that can post to `SLACK_CHANNEL`.

## Scope / next

- **Remediation is out of scope here by design.** Closing a finding (an IaC/config
  PR, a people/process step) is a separate, human-gated job; this agent stops at
  a tracked, reported finding.
- **Close-the-loop verify** — confirming a merged fix flipped a Drata test green
  on the next sync is a natural follow-on.
