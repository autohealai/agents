---
name: service-inventory
description: >-
  Decide which domains a project holds, where the truth about its services, owners and dependencies lives, and import that into the Context Graph. Load on a first run and when the service list may be out of date.
---

# Domains and the service inventory

Agents answer "what is this service, who owns it, what does it call" from the Context Graph. That only works when the graph mirrors one agreed source of truth per fact, and stays in step with it. This skill settles three things, in order: which domains the project holds, where the truth lives, and what to import.

Write what you settle into the readiness report (`./skills:context-readiness`), so the next run starts from it instead of asking again.

## 1. Which domains

A **domain** is one business area and the team that is on call for it, such as payments or market-data. A project usually holds one domain. It can hold a few when one on-call team runs them all. Two teams with separate on-call rotations belong in separate projects: a project's skills, integrations and permissions are shared by everyone in it.

Read before you propose. In parallel where you can, each call bounded by a limit:

- Context Graph: `context_graph_list_entities` with `blueprint: team`, and the imported team blueprints that have entities (`github_team`, `pagerduty_team`, `servicenow_team`, `datadog_team`). `context_graph_list_blueprints` lists what exists.
- Code host: the organization's teams and `CODEOWNERS` files (see the code host's reference in `./skills:integration-skill`).
- Paging and ticketing: PagerDuty services and escalation policies, ServiceNow assignment groups, Jira projects.
- Runtime: Kubernetes namespaces, cloud account or resource-group names, and their `team` or `owner` tags.
- Chat: channels named for a team or a service.

Then show a short table: each candidate domain, the evidence for it (which teams, repositories, services and channels point at it), and whether you recommend it for this project. Recommend; do not ask the person to invent the list. Confirm with `ask_user_input`. When something belongs in another project, say so and leave it out.

When the person already knows ("this project is payments"), confirm that one domain and skip the survey.

## 2. Where the truth lives

For each fact below, find the candidates, then agree one source with the person. Prefer the source that the team's own process keeps current (a file reviewed in pull requests, a CMDB that change management updates), that a machine can read, and that is most complete for this domain.

| Fact | Candidates, in the order to check |
|---|---|
| Services and components | ServiceNow CMDB (`servicenow_cmdb_ci`, `servicenow_service`); PagerDuty services; Datadog service catalog (`datadog_service`); service folders in a monorepo; Kubernetes deployments; a wiki page |
| Owners | `CODEOWNERS`; PagerDuty escalation policies; ServiceNow assignment groups; code host teams |
| Dependencies | An APM service map (Datadog, Dynatrace, Honeycomb); client and config code; the architecture doc |
| Repositories | the code host's import (`github_repository`, `gitlab_repository`, `bitbucket_repository`, `azuredevops_repository`) |
| Tier | CMDB business criticality; PagerDuty urgency; a scorecard; otherwise ask |
| On-call and channels | PagerDuty or the on-call tool's schedules; Slack channels |

How to look:

- Imported blueprints first: list a few entities of each with `limit: 5`, and count them. An imported blueprint with entities means that integration already syncs into the graph.
- Files in code: read `CODEOWNERS` and the deploy manifests (Helm values, Kubernetes manifests) in the domain's repositories.
- The integrations' own read tools for the rest.

Show, for each fact, what you found (the source, how many items, two or three examples), your pick and why, in one table. Confirm with `ask_user_input`. Record the agreed sources in the `Sources` section of `<domain>-architecture`, and in the readiness report.

The rules that follow from it:

- The source wins. The Context Graph mirrors it. When they disagree, change the graph, not the source, and say what changed.
- Never hand-maintain a list that a source already keeps. A list in a skill goes out of date; a label or an import does not.
- When the agreed source is an integration that the Context Graph imports but its blueprint has no entities, the import has not run or fails. Say so and point the person to that integration's page. Do not copy its items by hand.

## 3. Import

What to write, and how, is in `./skills:onboard-project`'s `references/context-graph.md`. In short:

- **The source is an imported integration** (its blueprint has entities): create one `service` entity for each of the domain's components, with `owner` set to the team, and link the imported entity to it with `team` and `service` labels. Do not copy the integration's whole inventory: only the domain's part.
- **The source is a file or a page** (`CODEOWNERS`, a wiki table, Kubernetes manifests): read it, build the list, and show it as a table (name, title, owner, tier, repository, depends on, and where each row came from). After the person confirms, write it with `context_graph_write`, at most 25 entities a call, with `source: {"integration_type": "onboarding", "metadata": {"skill": "service-inventory", "from": "<repo>/<path> or <tool>"}}`.
- Use the source's own names for `name`, byte for byte (lowercase with dashes where the source allows it), so the next import matches the same entity instead of creating a second one.

On a later run, compare the source with the graph and show three lists: new in the source, changed, and gone from the source. Write the new and changed ones after the person confirms. For the ones that are gone, list them and say that they can be deleted on the Context Graph page; you do not delete entities.

After each write, say what landed, from the tool's result: `created`, `updated`, `unchanged` or `failed` for each item, and why an item failed.
