---
name: context-readiness
description: >-
  Score how ready a project's context is for incident response, list what is pending in order, and keep the readiness report that each run updates. Load at the start and end of every run.
---

# Context readiness

Three things, every run: a **score** out of 100 that says how well the project's agents could handle an incident today, the **pending list** that says what would raise it, and the **readiness report**, one artifact per project that each run reads first and updates last.

## 1. Read the last report

At the start of a run, find the report: `list_artifacts` with `query: "Context readiness"` and `kind: report`, then the one whose name is `context-readiness-<project id>`. Read it with `get_artifact`. It holds the agreed domains and sources of truth, the last score, the pending list and the decisions made so far. Build on it: do not ask again what it answers.

When there is none, this is the project's first run.

## 2. Score

Score each domain separately, from what you read **in this run**. A check is met (full points), partly met (half, or the share stated) or not met (0). Never give points for something you did not read in this run, and never for a skill section that is mostly `> INCOMPLETE:` marks. Count a check that does not apply (no database in scope) as met, and say so.

| # | Area | Points | Met when |
|---|---|---|---|
| 1 | Integrations work | 10 | 2 each for alerts, logs, metrics, code, and deploy history: a connection of that kind returned data to a read in this run. Partly: connected but the read failed. |
| 2 | Domains and owners | 10 | Domains agreed and recorded (3). A `team` entity for the domain (3). Every domain service has `owner` set to it (2). The team has a notification channel (2). |
| 3 | Service inventory | 15 | Source of truth agreed and recorded (4). Every component that the source lists for the domain is a `service` entity (5, by share). Each has a `tier` (3). `depends_on` set between them (3). |
| 4 | Integration skills | 20 | `skills/<type>/SKILL.md` with the domain's section, for each connected integration that an investigation uses: alerts, logs, metrics, traces, code, deploys, tickets, chat (12, by share). Their queries and filters ran (8, by the share of patterns without `UNVERIFIED` or `UNTESTED` marks). |
| 5 | Domain knowledge | 15 | `<domain>-architecture` (5). A component skill for each of the top three to five components (6, by share). `<domain>-data` when a database is in scope (2). No `INCOMPLETE` marks left in these (2, by share). |
| 6 | Code | 10 | The domain's repositories carry `team: <domain>` (4). `<domain>-codebase` says how each component deploys and how to find the change before an incident (4). `repository_url` on the services (2). |
| 7 | Alert routing | 10 | The alert source's field that names the component or domain is recorded and was tested (5). Of the alert groups of the last 30 days (`list_alert_groups`), the share that names a known service (5). |
| 8 | Incident history | 10 | `<domain>-incident-patterns` (4). Past incidents or postmortems are in Autoheal (`list_incidents`, or incident entities in the Context Graph) (2). Proven: a run of the project's incident or triage agent on a resolved incident found the known cause (`list_agent_runs`, then `read_agent_run`) (4). |

Bands: **0–39 not ready**, **40–64 ready to try** (a first investigation will work with gaps), **65–84 ready**, **85–100 well covered**. Area 8's "proven" check is the real test: the score is a guess until an agent has solved a real, resolved incident from this context.

Also say, in one line each, how ready the project is for its other uses:

- **Code review**: the code host works, `<domain>-codebase` exists, owners are known (`CODEOWNERS` or the Context Graph), and the team's review conventions are written down.
- **Questions**: the architecture skill exists, the domain's docs were read, and the services are in the Context Graph.

## 3. The pending list

Collect the gaps: unmet checks, `INCOMPLETE`, `UNVERIFIED` and `UNTESTED` marks in the domain's skills, connections that fail, and the open questions for the team. For each one, write the points it would add, who can do it (you in this conversation, the person, or someone else, named by role, such as "the Datadog admin"), and roughly how long it takes.

Order by points gained for the effort, and split it:

- **Next**: the top three. The first one is your recommendation for what to do now.
- **Later**: the rest.
- **Blocked**: what waits on someone else, with who to ask and what to ask them.

Lead the person in one direction. End the turn by offering the first "Next" item as the first `ask_user_input` option.

## 4. Update the report

At the end of every run, and also when the person stops early, write the report: `create_artifact` on a first run (`kind: report`, `name: context-readiness-<project id>`, `title: Context readiness: <project title>`), otherwise `update_artifact` with the report's id, the complete new `content`, the `expected_version` you read, and a `change_note` such as `Score 42 → 58: logs skill tested, 6 services imported`. Each update keeps the old version, so the history is never lost.

```markdown
# Context readiness: <project title>

**<score>/100, <band>** (was <last score> on <last date>)

Domains: <domain> (<team title>), …
Code review: <ready / partly / not ready>, <one reason>. Questions: <…>, <one reason>.

## Score
| Area | Points | Evidence |
|---|---|---|
| Integrations work | 8/10 | logs, metrics, code, deploys read OK; alerts: PagerDuty 401 |
| … | | |

## Next
1. <action> (+<points>, <who>, <time>)
2. …
3. …

## Later
- …

## Blocked
- <what> — ask <who>: <question>

## Sources of truth
| Fact | Source | Notes |
|---|---|---|

## Decisions
- <date>: <what was decided, by whom>

## What this context holds
- Skills: <list, each with its path>
- Context Graph: <n> services, <n> repositories labelled, team <name>

## History
| Date | Score | What changed |
|---|---|---|
```

Keep the History and Decisions rows from the last version and add this run's row on top. Write dates as `YYYY-MM-DD`.
