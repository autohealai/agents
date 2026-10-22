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
| [`incident-response`](agents/incident-response/) | Investigates a production incident end to end: gathers evidence, commits to one root-cause conclusion, has a private verifier agent try to disprove it, and reports the cause with evidence and proposed mitigations. Read-only. |
| [`incident-investigation`](agents/incident-investigation/) | Investigates a production incident end to end: gathers evidence from the connected observability and deployment sources, tests competing explanations through its own subagents, and proposes a bounded mitigation. |
| [`release-readiness`](agents/release-readiness/) | Reads a release candidate and its change diff, checks migrations, canary and rollback plan through its own subagents, and returns a ship-or-hold verdict with the blocking risks and the team that owns each one. |
| [`vulnerability-remediation`](agents/vulnerability-remediation/) | Triages a dependency or container advisory against how the code actually uses it, works out whether the vulnerable path is reachable, and proposes the smallest change that closes it. |
| [`cloud-cost-optimization`](agents/cloud-cost-optimization/) | Starts from the bill rather than the resource list, attributes each of the largest lines to the service and team that caused it, and only then looks for what could change. |
| [`alert-triage`](agents/alert-triage/) | When a new alert group fires, links the alerts that fired alongside it through the service dependency graph and pages the owner of the cause once. Flags noisy monitors and proposes a threshold change. |
| [`deploy-verification`](agents/deploy-verification/) | After each production deploy, compares error rate, latency and SLO burn with the pre-deploy baseline and the same hour last week. On a regression it can attribute to the change, it pages the owner and opens a revert PR. |
| [`runbook-execution`](agents/runbook-execution/) | When a known alert fires, runs the approved runbook for it once, then checks recovery against the service's SLO for 15 minutes before resolving. If the service has not recovered, it escalates to on-call with a log of every action taken. |
| [`critical-cve-patching`](agents/critical-cve-patching/) | When a critical (zero-day) advisory is published, finds every repository, image and running workload that carries the package, gets the scope approved, opens a patch PR per repository, and posts hourly status to #security-leadership until nothing running carries it. |
| [`pr-risk-review`](agents/pr-risk-review/) | Reviews every pull request against main using the service's tier, incident history, SLO and production traffic, scores its risk from 0 to 100, picks reviewers from the catalog, and checks database migrations against the real table size and write rate. |
| [`service-scorecard`](agents/service-scorecard/) | Every week, checks each service against the platform team's scorecard (on-call, SLO, monitors, runbook and so on). For a failing rule it opens a pull request in the owning repository, with SLO targets taken from the service's own 28-day history, and closes the ticket once the rule passes. |
| [`coding-agent-spend`](agents/coding-agent-spend/) | Every night, prices the coding agents' token usage by type, compares your repositories on cost per merged PR, and finds where each one's tokens go. It opens the fix as a PR: an ignore rule for the owning team, or a benchmarked settings change for platform engineering. |
| [`eol-upgrades`](agents/eol-upgrades/) | Upgrades every repository in a migration off an end-of-life runtime, toolchain or base image. Tests the upgrade steps on one pilot repository per language first, then opens the rest tier by tier once the platform lead approves. A repository counts as done when production runs the new image. |
| [`service-scaffolding`](agents/service-scaffolding/) | Creates a repository for a new-service request from the approved (golden-path) template, and checks it against the six scorecard rules before handing it over. Also opens pull requests that move older scaffolds to the current template. |
| [`cost-anomaly-triage`](agents/cost-anomaly-triage/) | For each daily Vantage cost anomaly, finds the deploy, config change, scaling event or traffic change that caused it, names the owning team, and proposes a fix with its dollar impact, as a pull request when the resource is declared in code. |
| [`pr-review-reminders`](agents/pr-review-reminders/) | Keeps one Slack thread per open pull request in your organisation with its review status and who it is waiting on. Reminds only that person, reviewer or author, during their working hours, and suggests a reviewer from CODEOWNERS and the catalog when nobody was requested. |
| [`support-escalation-triage`](agents/support-escalation-triage/) | When support escalates a Pylon ticket to engineering, replays the customer's own session, errors and logs, and matches them to a known issue by stack trace and release. Drafts the reply for support, or files a reproducible Jira bug to the owning team when the failure is new. |

## How to use an agent

1. Open the agent's folder and its `agent.yaml`.
2. Copy the file contents.
3. In Autoheal, create a new agent and paste the YAML into the editor.
4. If the folder has an `agents/` directory, the agent has private child agents.
   Create each one in the agent's file tree at the same path (for example
   `agents/incident-verifier/agent.yaml`) and paste its file in. The agent's
   README says so too.
5. Replace any placeholders (e.g. the Slack channel), connect the integrations the
   agent references, then save and run.

## Repo layout

```
agents/
  <agent-name>/
    agent.yaml     # the agent spec — copy this into the editor
    README.md      # what the agent does and what it needs
    catalog.yaml   # apiVersion agents only: catalog fields (not part of the agent)
    agents/        # apiVersion agents only: private child agents, if any
      <child>/agent.yaml
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
