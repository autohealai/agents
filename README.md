# Autoheal Agents

A public library of ready-to-run agents for the [Autoheal](https://autoheal.ai) platform.

Each agent is a single `agent.yaml` you can **copy and paste into the Autoheal agent
editor** to get running in seconds. Browse the folders below, open an agent's
`agent.yaml`, copy it, and paste it into a new agent in the product.

Agents here come from both the Autoheal team and the Autoheal community — anyone can
[contribute one](CONTRIBUTING.md) by opening a pull request.

## Agents

| Agent | What it does |
|-------|--------------|
| [`azure-ai-cost-weekly`](agents/azure-ai-cost-weekly/) | Posts a weekly estimate of Azure AI (Foundry / Azure OpenAI) LLM spend to a Slack channel, broken down by model. |
| [`gcp-ai-cost-weekly`](agents/gcp-ai-cost-weekly/) | Posts a weekly estimate of GCP Vertex AI LLM spend to a Slack channel, broken down by model. |
| [`aws-ai-cost-weekly`](agents/aws-ai-cost-weekly/) | Posts a weekly AWS Bedrock/Claude LLM cost report (all accounts) to a Slack channel, with week-over-week change. |
| [`vulnerability-remediator`](agents/vulnerability-remediator/) | Turns a container-image vulnerability worklist into reviewable PRs/issues (API-only, no checkout) — never merges, deploys, or rebuilds live images. |
| [`drata-compliance-reporter`](agents/drata-compliance-reporter/) | Runs the weekly Drata compliance review — reads control readiness and every failing monitoring test, maintains a rolling tracker issue with one sub-task per finding, and posts a Slack digest. Reports and tracks only — never changes code or edits Drata. |
| [`pr-reviewer`](agents/pr-reviewer/) | Reviews every opened/updated pull request for correctness, security, and maintainability and posts one structured review comment — never edits, approves, or merges. |
| [`flaky-test-detective`](agents/flaky-test-detective/) | Scans recent GitHub Actions CI on a schedule, catches flaky tests via same-commit pass/fail flips and rerun-recoveries, files a tracking issue per flake, and posts a Slack scoreboard — never disables a test or merges. |
| [`flaky-test-weekly-rollup`](agents/flaky-test-weekly-rollup/) | Posts a weekly CI-reliability summary to Slack — flaky rate with week-over-week trend, CI time wasted on reruns, and flaky-backlog progress. Read-only trend companion to `flaky-test-detective`. |
| [`smart-pr-reviewer`](agents/smart-pr-reviewer/) | Routes each PR to the right reviewers — scores change risk from a criticality map, picks owners from CODEOWNERS + recent file history, requests them, and comments why. Never edits, merges, or (by default) approves. |

## How to use an agent

1. Open the agent's folder and its `agent.yaml`.
2. Copy the file contents.
3. In Autoheal, create a new agent and paste the YAML into the editor.
4. Replace any placeholders (e.g. the Slack channel), connect the integrations the
   agent references, then save and run.

## Repo layout

```
agents/
  <agent-name>/
    agent.yaml     # the agent spec — copy this into the editor
    README.md      # what the agent does and what it needs
catalog.json       # generated index of every agent (do not hand-edit)
scripts/
  validate_agents.py   # CI: validates every agent.yaml
  build_catalog.py     # CI: regenerates catalog.json
```

`catalog.json` is a machine-readable index of every agent (category, trigger,
required integrations, and the full `agent.yaml` inline). It is generated from the
agent manifests — run `python scripts/build_catalog.py` after changing an agent and
commit the result. CI fails if it is out of date.

## Contributing

Anyone can add an agent — Autoheal or an Autoheal customer. Open a pull request
with a folder under `agents/<agent-name>/` containing an `agent.yaml` and a short
`README.md`. CI validates every agent and a maintainer reviews before merge. See
[CONTRIBUTING.md](CONTRIBUTING.md) for the format and the rules (keep it generic,
no secrets, no tenant-specific IDs).

Licensed under [MIT](LICENSE).
