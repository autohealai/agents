# Context Setup

Interviews you to set up and improve a project's context, so that the project's agents can handle a real incident, review a change and answer questions about your systems. Incident response comes first.

Run it on day 0 to set a project up, then again on day 1, in week 1 and whenever your systems change. Each run reads the readiness report the last run left, scores the project out of 100 and works down the list of what is still missing.

## What it does

1. **Takes stock.** Reads the project's connections (and checks each one returns data), its skills, its integration context forms, old guides and runbooks, and the Context Graph.
2. **Agrees the domains.** Proposes which domains (business area plus the team on call for it) the project should hold, from your teams, `CODEOWNERS`, paging services and channels.
3. **Agrees the sources of truth.** For services, owners, dependencies, repositories, tiers and on-call, finds the candidates (ServiceNow CMDB, PagerDuty, Datadog's service catalog, `CODEOWNERS`, Kubernetes, a wiki page) and recommends one for each.
4. **Imports.** Writes the domain's team and services, with owners, tiers and dependencies, into the Context Graph, and labels the domain's repositories. On later runs it shows what changed in the source and syncs it.
5. **Interviews you, one category at a time:** components, alert sources, logs and traces, metrics, cloud runtime, code, deploys, data stores, ticketing, comms and incident history. It explores each connected integration first, so you confirm what it found instead of describing it.
6. **Writes skills for your agents:** one per integration (`skills/<type>/SKILL.md`, with the domain's tested queries and filters) and the domain's own (`<domain>-architecture`, a skill per key component, `<domain>-codebase`, `<domain>-data`, `<domain>-incident-patterns`). Each one is written for an agent in the middle of an incident: what to check first, the exact filter for a component, and how to find what changed.
7. **Scores the context** out of 100 across eight areas (integrations, domains and owners, service inventory, integration skills, domain knowledge, code, alert routing, incident history), lists what is pending in order of value, and recommends one next step. It also says how ready the project is for code review and for questions.
8. **Keeps a readiness report**, an artifact named `context-readiness-<project id>` that each run updates. Its versions are the history of the score.

## Files

```
agents/context-setup/
  agent.yaml
  catalog.yaml
  instructions.md
  skills/context-readiness/SKILL.md
  skills/service-inventory/SKILL.md
  skills/onboard-project/SKILL.md
  skills/onboard-project/references/code-exploration.md
  skills/onboard-project/references/context-graph.md
  skills/onboard-project/references/question-bank.md
  skills/onboard-project/references/skill-shapes.md
  skills/integration-skill/SKILL.md
  skills/integration-skill/references/<type>.md   (one per integration type)
```

Every agent here uses the `apiVersion: agents.autoheal.ai/v1` format. The agent lists no `skills`, so it gets its own four skills and every skill in your project. It names no `model`, so it runs on your organization's default; it works best on a strong model with high thinking, and `agent.yaml` has a commented-out `model` block to pin one.

## Use it

1. In Autoheal, create an agent named `context-setup` and paste [`agent.yaml`](agent.yaml) into its editor.
2. In the agent's file tree, create `instructions.md` and paste [`instructions.md`](instructions.md) into it.
3. Copy the `skills/` folder into the agent's file tree at the same paths.
4. Connect what you can first: alerts, logs, metrics, your code host, tickets and chat. It works with whatever is connected and gives you a connect link for the rest.
5. Run it by hand and talk to it: `autoheal run context-setup "Set up context for this project"`, or start it from the agent's page. Answer its questions on the run's page, or with `autoheal runs answer`.
6. Run it again later with "review my setup" to see the score and continue from the gaps.

## Safety

Its instructions keep it from changing a connected system: it uses integration tools and the shell only to read. In Autoheal it writes skills under `skills/` (one commit per skill, only after you say "Commit it"), Context Graph entities and integration context forms (after you confirm the list), and its own readiness report. It never deletes anything, never writes another agent's files, and never asks for or prints a credential.
