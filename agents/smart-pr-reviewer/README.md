# Smart PR Reviewer Assignment

Routes every pull request to the **right reviewers**. On each PR it scores how risky the change is,
picks the humans who actually own the touched code, requests them as reviewers, and posts one short
comment explaining the pick. It only **reads** the repo, **requests reviewers**, and posts **one
comment** — it never edits code, pushes, merges, or (unless you explicitly enable it) approves. A
human always does the actual review.

Reviewer choice is evidence-based, not guessed: **CODEOWNERS** for the touched paths first, then a
**recent-file-history** fallback (who last committed to the changed files) — all via the GitHub API,
no clone. Risk comes from a **criticality map** you edit (globs → low/medium/high/critical), so it
needs no external catalog or blueprint to run.

## What it does
1. Runs on a schedule (or a PR event, when available) — no input to type, never asks for a PR number.
2. Discovers open PRs updated recently and **self-gates**: skips drafts, PRs that already have
   reviewers, and PRs it already handled (a hidden marker in its own comment).
3. Scores the PR's **criticality** from the changed files against your glob map.
4. Builds a reviewer shortlist: **CODEOWNERS** owners first, then recent committers of the changed
   files. Drops the author and bots, caps at `MAX_REVIEWERS`.
5. **Requests** the chosen reviewers on the PR.
6. Posts **one comment**: the risk level, what decided it, and who it requested and why.

## Use it
1. Copy `agent.yaml` into a new agent in Autoheal.
2. Edit the block at the top: set `REPO`, tune the `CRITICALITY MAP` globs, and optionally
   `MAX_REVIEWERS`, `SCAN_MINUTES`, `MAX_PRS_PER_RUN`, `AUTO_APPROVE`.
3. Connect the **GitHub** integration and grant **write** — it requests reviewers and comments.
4. Add a **Schedule** trigger (e.g. every 20 min) and match `SCAN_MINUTES` to it. When a PR-event
   trigger is available, the same agent runs event-driven with no change.
5. Run it once manually against a test PR, read the comment and the requested reviewers, then activate
   the schedule.

## Model
The YAML ships with `gpt-5-mini` at high reasoning effort. The agent is **model-agnostic** — its
instructions use no provider-specific features and it drives the `gh` CLI — so it runs on any approved
LLM out of the box. Swap it in the builder's Budget or edit the `model:` field.

## Needs
- **GitHub integration** with **write** access — the sandbox injects its credentials so `gh` can read
  the PR/diff/CODEOWNERS/history and request reviewers + comment.
- A **CODEOWNERS** file helps but is optional — without one it falls back to recent file history.

## Notes
- **Never merges or edits.** The most it does is request reviewers and post one comment. Approval is
  **off by default**; the optional `AUTO_APPROVE = low-only` flag is guarded (docs-only, tiny, never
  high/critical) because an approval can satisfy branch protection and merge code with no human.
- **Idempotent.** A hidden marker in its comment plus the "already has reviewers" check mean repeated
  runs never double-assign or double-comment.
- **No clone, no catalog.** Reviewer history uses the commits API (returns GitHub logins directly) and
  criticality is a local glob map — nothing to provision.
- **Schedule today, event-ready.** Custom agents run on Manual/Schedule, so it discovers PRs on a
  cron; the day a PR-event trigger exists it runs event-driven with no change to the YAML.
- **Governance.** If a policy gates every write on human approval, the reviewer request and comment
  pause as "waiting for input" until approved.
