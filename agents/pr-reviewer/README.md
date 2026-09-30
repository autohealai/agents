# PR Reviewer

Reviews every opened or updated pull request for correctness, security, and maintainability, and
posts **one structured review comment** back on the PR. It reviews only — it never edits files,
approves, requests changes as a gate, or merges. A human decides.

It reads the diff, the changed files, and their callers/tests through the authenticated GitHub
CLI/REST, then posts a single review comment. If the sandbox has a checkout it can also run the
repo's cheap linters/type-checks; otherwise it relies on CI and says so.

## What it does
1. Starts on a PR event with the repo and PR number (no input to type).
2. Skips if it has already reviewed this exact head commit (no duplicate reviews on re-runs).
3. Reads the diff, then each changed file in full at the PR head, plus callers, tests, and
   interfaces it touches. For very large PRs it scopes to the highest-risk files and says so.
4. Reviews against the PR's intent, in priority order: correctness → security → data/API
   integrity → performance → tests → maintainability.
5. Posts one review comment: summary + advisory verdict, then Critical / Warnings / Suggestions /
   Questions, each finding cited by `file:line` with a concrete fix, plus what it verified.

## Use it
There are **no placeholders to edit** in `agent.yaml` — the repo and PR come from the trigger.
1. Copy `agent.yaml` into a new agent in Autoheal.
2. Connect the **GitHub** integration and grant it **write** (to post the comment) plus read.
3. Add a trigger that fires **when a pull request is opened or updated**. Confirm the exact
   PR-event options your SCM exposes in the builder; if only "merged" is available, use the
   CI-webhook fallback below.
4. (Optional) Change the model in the builder's Budget — see **Model**.
5. Test on one PR (run it manually with a repo + PR number), read the comment it posts, then
   activate the trigger.

## Model
The YAML ships with `gpt-5-mini` at high reasoning effort. The agent is **model-agnostic** — its
instructions use no provider-specific features and it drives the `gh` CLI — so it runs on any
approved LLM (OpenAI, Anthropic, or your own) out of the box. Swap it in the builder's Budget or
edit the `model:` field; `thinking: high` maps to the provider's reasoning setting automatically.
Review quality tracks reasoning depth, so prefer a strong reasoning model.

## Needs
- **GitHub integration** with **write** access — the sandbox injects its credentials so `gh` can
  read the PR and post the review comment. (Reads and writes go through the `gh` CLI, which is
  always available in the sandbox; connecting the integration is what authenticates it.)
- Nothing else. No Slack, no cloud accounts.

## Notes
- **Reviews, never blocks.** It posts a plain comment (`gh pr review --comment`), never
  `--approve` or `--request-changes`, so it never changes the PR's merge state. The verdict is
  advice in text. If the bot identity is the PR author, it falls back to a plain PR comment.
- **Governance.** If a policy gates every write on human approval, the review comment pauses as
  "waiting for input" until approved — exempt PR comments for a fully hands-off flow.
- **CI still owns build/test/lint** unless a checkout is available; the agent states exactly what
  it ran and never implies a check passed that it didn't run.

## Advanced: trigger from CI
The native PR-event trigger above is the recommended path for almost everyone. Reach for a
CI-driven trigger only if you need to **gate the review on CI results** (review after tests pass),
your SCM **can't send PR webhooks** to Autoheal (some self-hosted/air-gapped setups), or you need
**selection logic** the native filter can't express. In those cases, start the same agent from a
GitHub Action (or any CI job) via an inbound **webhook**, the **CLI**, or **MCP**, passing the repo
and PR number as the run input. The `agent.yaml` is unchanged.
