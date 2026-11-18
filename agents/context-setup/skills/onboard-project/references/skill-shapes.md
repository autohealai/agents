# Skill shapes

A template for each skill that onboarding writes. Use the headings in the template. Leave out a section that has nothing in it, but keep a section that you know is missing and mark it `> INCOMPLETE:`.

## What every skill needs

````markdown
---
name: <Display name>
description: >-
  <under 200 characters: what it covers, and when an agent loads it>
labels:
  - team: <domain>
---
````

- The folder name is the skill's id: `skills/<id>/SKILL.md`, lowercase with dashes. `name` is the display name.
- `description` is how an agent decides to load the skill: say what it covers and when to load it, such as "Load when an alert or ticket names <component>". Keep it under 200 characters. Write it as a folded block (`description: >-`, then the text on the next line, indented), as in the templates: a colon followed by a space in a plain one-line value is invalid YAML, and the skill then does not load.
- `labels` is a list of `- key: value` items. Repeat a key for each value. The `team` value is the team entity's name, byte for byte.
- Write for the agents that investigate, not for the person in this conversation. Name the integration's own tools, CLIs, query languages and field names. Do not name your own tools or `project_id`.
- Put each query in a fenced block with its language, then one line on what it returned when you ran it.
- Keep it to stable facts: one or two pages. No dates of this session, no "as discussed".
- Say where each fact came from (rule 8) where a reader could doubt it: a short `(from …)` at the end of the line, or a `Sources` section.

## `<domain>-architecture`

````markdown
---
name: <Team title> architecture
description: >-
  The <title> domain: what it does, its components, data flow, critical paths and dependencies. Load first when investigating any <title> incident.
labels:
  - team: <domain>
---

# <Team title> architecture

## What the domain does
<Two to four sentences on the business flow: what comes in, what the domain does with it, what goes out, and who notices when it stops.>

## Components
| Component | What it does | Runs on | Skill |
|---|---|---|---|
| <name> | <one line> | <AKS namespace / EC2 / on-premises hosts / a batch scheduler> | `<component skill id>` |

<Subdomains, if any: one line each and the components in each.>

## Data flow and critical paths
<Numbered steps of the main flow, naming the component at each step and whether the step is real-time or batch (with its schedule). Then the critical paths: which step, if it stops, costs the business what, and how soon.>

## Upstream and downstream systems
| System | Direction | What passes | Owner | How to tell it is the cause |
|---|---|---|---|---|

## Data stores
<Each database or store and the components that use it. Details in `<domain>-data`.>

## Environments and regions
<Environments, regions, hours of operation, batch windows. Where host inventory lives when there is no single inventory.>

## Outside the team's control
<Shared platforms, vendors and other teams' services on the critical path, and how to reach their owners.>

## Sources
- <doc title> — <link> (doc-derived)
- Interview with <role>, <what they described> (user-described)
- <repo> (from code)
````

## A component: `<component>`

Only for the components to cover first. Use the service entity's name as the id when it is a valid id.

````markdown
---
name: <Component title>
description: >-
  <Component> in the <title> domain: what it does, where its logs, metrics and code are, and how it fails. Load when an alert, ticket or log names <component>.
labels:
  - service: <service entity name>
  - team: <domain>
---

# <Component title>

<What it does, in two or three sentences. Upstream and downstream components.>

## Code
<Repository and paths, entry point, configuration files. See `<domain>-codebase`.>

## Logs
<Integration and the tested query, with the component fixed and the environment and region as placeholders.>

```logql
{component="<component>", env="<ENV>", region="<REGION>"} |= "ERROR"
```
Ran on <date>: <count> lines in the last hour.

<Log message formats worth searching for, and the fields that carry business ids.>

## Metrics
<The golden signals with a tested query for each.>

## Dashboards
- <name> — <link>

## Failure modes
### <short name of the failure>
- Signs: <alert, log line, metric>
- Check first: <query or command>
- Usual cause and fix: <...>

## Owners
- <name or group> — <role>, <channel>
````

## An integration's domain section

The integration's own skill, `skills/<type>/SKILL.md`, holds what is true for the whole project. The domain's part goes under its own heading, so other teams' parts stay untouched. Follow `./skills:integration-skill` when you have it; otherwise this shape:

````markdown
## Team: <Team title>

Selects this domain: `<pattern with placeholders>`
Components: `<label or field>` = <values that exist, as the tool returned them>
Environments: <values>  Regions: <values>

Queries (ran on <date>):

```<language>
<query>
```
<what it returned>

Queries the team runs (verbatim):

```<language>
<pasted query>
```

Dashboards:
- <name> — <link>

> INCOMPLETE: <what is missing> (ask <who>)
````

Examples of a domain's pattern, by tool:

| Tool | The pattern |
|---|---|
| Grafana with Loki or Prometheus | label selectors, such as `{component="<COMPONENT>", env="<ENV>", region="<REGION>"}`; the data source name or uid |
| Dynatrace | the management zone, entity tags such as `[Kubernetes]app:<APP>`, a DQL `fetch logs` filter |
| Datadog | `service:<SERVICE> env:<ENV>`, and the team tag if there is one |
| ServiceNow | the assignment groups, the configuration item classes and names, the severity field and its scale |
| PagerDuty | the services and escalation policies |
| GitHub, GitLab, Azure DevOps | the organization, group or project, and the repositories (also in `<domain>-codebase`) |
| AWS, Azure | the accounts or subscriptions, the tag or name pattern, the regions, the Kubernetes namespaces |

## `<domain>-codebase`

````markdown
---
name: <Team title> codebase
description: >-
  Where the <title> domain's code is: repositories by component, entry points, configuration, log formats, deploy pipelines. Load when you need the code or the last change.
labels:
  - team: <domain>
---

# <Team title> codebase

## Repositories
| Repository | Components | Paths | Language and framework |
|---|---|---|---|

## Entry points
<For each component: the main file or class, HTTP routes or queue consumers, scheduled jobs.>

## Configuration and feature flags
<Config files by environment, where flags are set, which settings change behavior in production.>

## Logging
<The logging library and the message formats that help a log search, with an example line and the file that writes it.>

## Deploys
<Manifests (Helm charts, Kubernetes YAML, Terraform), pipelines and their files, and how a commit reaches production.>

## Find the change before an incident
<The exact steps: which pipeline or release list to read, how its version maps to a commit, and the command to list the commits between two releases.>
````

## `<domain>-data`

````markdown
---
name: <Team title> data stores
description: >-
  The <title> domain's databases: key tables, safe read queries, tables never to query, and access limits. Load before you query a <title> database.
labels:
  - team: <domain>
---

# <Team title> data stores

## Access
<Read-only or not, query timeout, approved queries only or not, hours to avoid.>

## Never query
- `<schema>.<table>` — <why: size, locks, sensitive data>

## Databases and key tables
| Database / schema | Table | Key columns | Used by |
|---|---|---|---|

## Safe read queries (verbatim)
```sql
<pasted query>
```
<what it answers, and its parameters>
````

## `<domain>-incident-patterns`

````markdown
---
name: <Team title> incident patterns
description: >-
  Recurring <title> incidents of the last <N> weeks, how each was diagnosed and fixed, and what to check first. Load when triaging a <title> incident.
labels:
  - team: <domain>
---

# <Team title> incident patterns

From <ticketing tool>, <assignment groups>, <date range>: <count> incidents.

## <pattern name> (<count> incidents, for example <ticket ids>)
- Signs: <how the ticket or alert reads>
- Check first: <queries or commands, in order>
- Cause: <usual cause>
- Fix: <what fixed it, and who can do it>
````

## Import an existing skill

The person can point to a skill, guide or runbook from a trial or a staging project:

- A file in another Autoheal project that they can read: `git_read_file` with that project's id.
- A file in a repository: read it with `bash` and the code host's CLI.
- Text that they paste.

Do not copy the file as it is. Decide where its content goes, and say so before you write:

- A guide for one integration goes into that integration's skill, in the domain's section.
- A runbook for one failure goes into the component skill's "Failure modes", or into `<domain>-incident-patterns`.
- A procedure that stands on its own stays its own skill. Keep its id unless it collides with a skill in the project; add `team: <domain>` to its labels.

Keep pasted queries verbatim. Values from the trial environment (host names, subscription ids, environment names) can differ here: ask, and replace them with placeholders where they vary. Run each query on this project's connection. Mark what you could not run `> UNTESTED: from <source>; <tool> is not connected`.
