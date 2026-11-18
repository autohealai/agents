---
name: onboard-project
description: >-
  Set up a project's context so its agents can investigate from day one: interview the person, explore their integrations and code, and write the domain's Git skills and Context Graph entries. Load it for "set up context", "onboard my project", "get started" or "review my setup".
---

# Onboard a project

A project holds one **domain**: one business area and the team that runs it, such as a payments platform or a risk-calculation system. Onboarding gets the domain to the point where the project's agents can investigate a real incident. They must know what the domain does, which components matter, how to find each component's logs, metrics, alerts, tickets and code, and how to find what changed.

You write two kinds of things, as you go:

- **Git skills** in the project, saved as your instructions say ("Saving a skill"): one skill per commit, after the person confirms it. The project's agents load a skill by its description.
- **Context Graph entries**, with `context_graph_write`: the domain's team, its components as services with an `owner` relation, `team` labels on its repositories, and its notification channels. These save at once, with no preview.

References. Load one with `load_skill`, this skill and the reference's path as `file`, when a step names it:

- `references/question-bank.md`: for each category, the question that matters, its follow-ups, and what to explore before you ask.
- `references/skill-shapes.md`: a template for each skill you write, and how to import an existing one.
- `references/code-exploration.md`: find, clone and read the domain's repositories.
- `references/context-graph.md`: the team, services, repositories, labels and channels.

## Rules

These rules apply in every step.

1. **Patterns, not values.** A filter is `{component="<COMPONENT>", env="<ENV>"}`, not `{component="pricer", env="prod"}`. A value breaks when an investigation touches another component or environment. A component's own skill names that component, but keeps environment and region as placeholders.
2. **Queries verbatim.** Store a query that the person pastes byte for byte, in a fenced block. Do not reformat it or "fix" it.
3. **Test before you write.** Run each query, filter and name on the project's connection before you write it, with a short time window and a limit, and say what it returned. A filter that returns nothing looks like a healthy service: when it ran but returned nothing, write it with `> UNVERIFIED: returned no rows on <date>`. For a tool that is not connected, write `> UNTESTED: <tool> is not connected`.
4. **Merge, never replace.** Several people can onboard the same domain, at different times. Read each file with `git_read_file` immediately before you write it, keep all of its content, and add or change only your part. When what you learned contradicts what is there, ask which is correct.
5. **Identifiers come from tools.** Find an entity, repository, service or label value with a tool and use it byte for byte. Never make up a slug and read it back: `context_graph_write` creates an entity that it cannot find, so a near-miss name makes a second, empty entity. An integration's service list is the whole company's: ask which part belongs to this domain.
6. **Label, don't enumerate.** Link things to the domain with labels (`team: <domain>`, `service: <name>`). A label also covers what people add later; a list of names goes out of date.
7. **Read before you ask.** Docs, wiki pages, tickets, code and the Context Graph answer many questions. Ask the person only what your tools cannot tell you, and show what you found so that they can confirm or correct it.
8. **Say where each fact came from**: `(from <doc title or link>)`, `(from code: <repo>/<path>)`, `(from <tool> query)` or `(user-described)`. A vague answer gets one follow-up question. If it stays vague, write what you have and mark it `> INCOMPLETE: <what is missing> (ask <who>)`.
9. **Keep moving, and write as you go.** A missing integration is a connect link and a recorded gap, not a reason to stop. Write the findings of each category when the category is done, so a session that stops early keeps its work. End each turn with the next question. Ask a question with options with `ask_user_input`, and start its question with one line of what you found or recorded: the card shows only the question and its options. Ask an open question at the end of your reply, after what you found.

## Step 0: Scope

The project is the one this run belongs to. Load `./skills:service-inventory` and follow its "Which domains" section to agree which domains the project holds; then work on one domain at a time, the one the person picks.

Then find the domain's team: `context_graph_list_entities` with `blueprint: team`. Match on meaning ("Payments", "payments-team" and "the payments squad" are the same team) and say in one line which case applies:

- **One match.** Name it: `Found the team "Payments" (payments)`. Its name is `<domain>` in every skill name and label below.
- **Several could match.** Ask which one with `ask_user_input`. Never choose for the person, and never create another one.
- **No match.** Propose a lowercase, hyphenated slug for the domain and confirm it with `ask_user_input`. Create the team when you write the first service (Step 6).

If the domain has subdomains (for example enrollments, payment execution and payment rails), keep them in this one team unless the person says that a subdomain has its own on-call team. Describe the subdomains in the architecture skill.

## Step 1: Inventory and readiness

Read what exists before you ask anything more. "Review my setup", or any second run, starts here and continues from the gaps. Never restart a setup that exists.

Read, in parallel where you can:

1. **Connections.** `list_integrations` lists the project's connected integrations; "connected" means configured, not working. For each one, call one of its read tools now (one page of services, projects, repositories or tickets) and note whether it returned data or the error. Never say that a connection works unless a read in this session returned data. A connection that fails is a gap: keep the error.
2. **Written context.** The project's skills are files in its Git repository, not in the project's machine: read them with `git_read_file`. For each connected integration type: its skill (`git_read_file` on `skills/<type>/SKILL.md`), its context form answers (`get_integration_context`), and its old guide (`get_agentsmd_integration_section`) and runbooks (`list_runbooks`). Also the project's skills (`git_list_files` on `skills/`), and the skills of an earlier onboarding: `<domain>-architecture`, `<domain>-codebase`, `<domain>-data`, `<domain>-incident-patterns` and the component skills. In those skills, the `> INCOMPLETE:`, `> UNVERIFIED:` and `> UNTESTED:` marks are the open gaps.
3. **Context Graph.** The team, the services that it owns, and the repositories labelled `team: <domain>`.

Then end the turn with your reply, not with `ask_user_input`. In a few lines: what exists and what you will reuse, which connections fail and why, and the open gaps. End with one open question: which tools the domain uses that are not connected (alerts, logs, metrics, tickets, wiki, code, chat), and whether skills, guides or filled-in context forms exist from a trial or a staging project that you should import.

When they answer, call `get_integration_setup` for each tool that is not connected and list it with its `connect_url` as a link. If Autoheal cannot connect a tool, say that its knowledge must come from people and docs. Read the material to import that they point to; see "Import an existing skill" in `references/skill-shapes.md`. On a second run, skip what the skills already answer and go to the open gaps: ask which one to work on first.

## Step 2: Read before you ask

Read the domain's own documentation before the interview: the pages that the person links, the pages that a wiki integration (Confluence, an Azure DevOps wiki, Notion) finds for the domain and its components, and the design docs and READMEs that they link to. Read them; do not only store the links. Keep each link to cite as a source.

## Step 3: Interview, one category at a time

Load `references/question-bank.md` and work through its categories in order. The person can skip a category with "skip" or "I don't know"; record a skipped category as a gap. Each category has the same five moves:

1. **Pick the integration.** Offer the connected integrations that fit the category. If none is connected, give the connect link, record the gap and go to the next category.
2. **Explore.** Get the real lists with the integration's own tools (services, label values, assignment groups, namespaces, projects), limited by a time window or a count.
3. **Narrow to the domain.** Show what you found and ask which part of it belongs to this domain (rule 5).
4. **Get the pattern.** Get the expression that selects the domain's data in that tool (rule 1), the dashboards that they open first, and the queries that they run, pasted (rule 2). Test the pattern (rule 3).
5. **Write it.** Write the domain's section of that integration's skill (Step 5) and confirm in one line what you recorded.

The first category, the domain and its components, decides what the rest is about. When a ticketing integration is connected, count the domain's incidents of the last 90 days by component, and offer the top ones. Otherwise, ask which components cause the most pages. Confirm which three to five components to cover first. Then write the architecture skill.

## Step 4: Code

Load `references/code-exploration.md` and follow it: rank the candidate repositories, ask which ones to read, clone each one with `bash`, read it with bounded commands, and confirm what you learned with the person before you write.

Do not skip this step when the code host is not connected or fails: ask for the repository URLs, because a public repository clones without a connection. Before you map a repository to a component, check that it is the domain's code: search it for the component names and the log messages from the interview.

## Step 5: Write the skills

Load `references/skill-shapes.md` for each skill's template. Write each skill when you have what it needs, not at the end:

| Skill | Write it when | Labels |
|---|---|---|
| `skills/<domain>-architecture/SKILL.md` | the domain category is done | `team: <domain>` |
| the domain's section of `skills/<type>/SKILL.md`, one for each integration | that integration's category is done | keep `integration: <type>` |
| `skills/<component>/SKILL.md`, one for each component to cover first | its logs, metrics and code are known | `service: <name>`, `team: <domain>` |
| `skills/<domain>-codebase/SKILL.md` | the code step is done | `team: <domain>` |
| `skills/<domain>-data/SKILL.md` | a database is in scope | `team: <domain>` |
| `skills/<domain>-incident-patterns/SKILL.md` | ticket history is read, or the person has said how they diagnose and fix the recurring incidents | `team: <domain>` |

For the integration sections, load `./skills:integration-skill` if it is offered to you and follow it. Without it, use the shape in "An integration's domain section" in `references/skill-shapes.md`. In both cases, put the domain's part under `## Team: <team title>`, and keep the other teams' sections.

Write each section from a tool result or from what the person said. When a skill would be mostly `> INCOMPLETE:` marks, ask its category's questions first (`references/question-bank.md`); a skill of empty headings costs the person a review and tells an agent nothing.

To save a skill:

- Use one commit for each skill, on the project's default branch, as your instructions say ("Saving a skill"). Before you commit, say in one line what the skill holds and get the person's go-ahead.
- A skill's labels also create their keys. Before the first commit that uses a label key that nothing has yet (`team`, `service`), say in one line that the key becomes available in the whole organization. "Label keys are shared" in `references/context-graph.md` says how to check.
- Read the file with `git_read_file` immediately before you write it, also when you read it earlier in the session (rule 4).
- Write `description` as a folded block (`description: >-`, then the text indented on the next line), as the templates do. A plain one-line description that contains a colon and a space is invalid YAML, and the skill does not load.
- After the commit, confirm in one line what was saved and continue. If the person declines because of a format problem, fix the file and propose it again.

## Step 6: Context Graph

Load `references/context-graph.md`. Write the team, one service for each component with `owner` set to the team, `depends_on` between components, `team` labels on the domain's repositories, and the team's notification channels. Confirm the list with the person before you write it.

You can also do this as you go: the services when the components are confirmed, the repository labels after the code step.

## Step 7: Readiness report

Write this report whenever the session ends: when the categories are done, when the person says to stop, and at the end of a "review my setup" run. Write it in the conversation, not in a file, plainly:

```
<Team title>: ready for a first investigation   (or: not ready yet, because <reason>)

Covered
  architecture   <domain>-architecture, from 2 wiki pages and the interview
  components     4 component skills: <names>
  alerts         <source>; the domain is in <field pattern>
  logs           <integration>, <pattern>, tested
  code           3 repositories, labelled team=<domain>; <domain>-codebase

Gaps
  <tool>         not connected: [Connect <tool>](<connect_url>)
  deploys        skipped

Open questions for the team
  - <question> (ask <who>)

Try it on
  <ticket id>: <short description>, resolved <date>
```

A domain is ready when it has the architecture skill, at least one component skill, the alert source's domain field, a tested log pattern, and its code mapped. Take the open questions from the `INCOMPLETE` marks. For "Try it on", pick a recent, resolved incident from the ticket history and name the project's triage or incident agent (`git_list_files` on `agents/`). Then ask with `ask_user_input` what to do next: run that agent on the incident (give the person the command, `autoheal run <agent> "<incident>"`), work on a gap, or stop. Say that "review my setup" continues from the gaps.
