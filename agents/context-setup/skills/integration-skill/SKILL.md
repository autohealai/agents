---
name: integration-skill
description: >-
  Set up an integration for a project: read its context form, explore the connected system, ask the person what tools cannot tell, fill the form and write or update the integration's skill, skills/<type>/SKILL.md. Load it before you curate an integration's context or write its skill.
---

# Integration skills

An integration skill, `skills/<type>/SKILL.md` (`skills/github/SKILL.md`), tells a project's agents what is specific to this customer's connection of one integration: what is connected, where things live under the customer's own names, queries that work, and the pitfalls to avoid. A project has one per integration type, and its agents load it when they work with that integration. The integration's context form (`get_integration_context`) is the structured record of the same setup, which people edit on the integration's **Context** tab; you fill it as you go and write the skill from it and from what you find.

Follow this skill whenever the person asks you to set up, curate, explore or fill in an integration's context, or to write or update an integration's skill, including a conversation that opens after a context form was submitted.

References: one per integration type, `references/<type>.md` (`references/dynatrace.md`), with what to capture for that integration, what to ask, its tools' and CLI's guardrails, and its pitfalls. Load the one for this integration (`load_skill` with this skill and the reference's path as `file`) before you explore. There is one for: azure, azuredevops, bitbucket, clickhouse, confluence, datadog, dynatrace, elasticsearch, fullstory, github, gitlab, grafana, honeycomb, mssql, notion, opensearch, postgresql, posthog, pylon, rivermuse, sentry, servicenow, slack, temporal, vantage. For any other type, follow this skill alone.

## 1. Pick the integration and the project

- One integration type at a time. When the person asks for several, finish one (its skill committed or declined) before you start the next.
- The project is the one this run belongs to. The integration must be connected in it: `list_integrations` lists the project's connections. When it is not, call `get_integration_setup` and give its `connect_url`, then stop.
- When the project has two or more connections of the type, pass `integration_name` on every call and cover each one. The skill covers them all: one subsection each where they differ (an EU and a US tenant), shared facts once.

## 2. Read what is already recorded

- `get_integration_context` for the type: the form's `schema`, its answers (`formData`) and its `content_hash`. When the form starts with a `features` table, work only on the features whose row is `selected: true`, or on every feature you can reach when none is.
- `git_read_file` on `skills/<type>/SKILL.md` in the project's default branch. When it exists, you are updating it (section 6).
- The project's old guide for the type (`<type>-guide`), saved before skills were Git skills: `get_agentsmd_integration_section` for the type. Reuse what still holds. When the person asks to move it into the skill, merge it in as an update (section 6) and leave deleting the old guide to them.
- Load `references/<type>.md`.

## 3. Explore the connected system

- Use only tools and commands that read: the integration's read tools and `bash` in the project's machine. Bound each call by a time window or a limit. Never call a tool or run a command that changes the connected system while you set it up.
- The first `bash` result from a project's machine carries each CLI's settings, such as a GitHub organisation or an Azure DevOps organisation; when it has none, discover them or ask.
- Follow the reference's guardrails: they are the calls that fail on this integration.
- Run each query, filter, name and id on the connection before you write it down. When a call fails or returns nothing, say what you ran; never write it as a fact.

## 4. Fill the form

The form saves as soon as you call `update_integration_context`, with no preview, so fill it only within this setup, and only from what a tool returned or the person told you.

- Each field's `x-editable-by` says what you may change: `agent`, write it; `both`, fill it only where it is blank; `user` or `none`, leave it. A suggestion for a `user` field goes in that feature's `agent_findings`.
- Keep existing table rows and append new ones. Leave `selected` for the person.
- A dropdown whose schema allows you to add options (`x-agent-can-populate-options`): append options, never replace the list, and leave the chosen value to the person.
- Send the complete new context with the `content_hash` you read. When the hash is refused, read the form again and redo your change on it.

## 5. Ask the person what tools cannot tell

Some facts live only in people's heads: which services matter, which environment is production, which pipeline deploys it, who owns what, which alerts are noise. The reference lists the ones that matter for this integration.

- Ask only what the form and your tools did not answer and what changes what the skill says. Ask in one message, the questions that matter most first, three at most; use `ask_user_input` when the answers fit short options (which of these repositories run in production).
- Before you ask, say in a few lines what you found, so the person answers against it.
- When the person says to go ahead without answering, write what is confirmed and say what is still open.

## 6. Write or update the skill

Save it like any other skill, as your instructions say ("Saving a skill"): one commit on the project's default branch, with the file's complete content and a one-line message, after the person confirms it.

- **Updating:** you read the file in section 2. Edit it rather than replace it: keep what people wrote by hand, change only what is out of date or missing, and keep every `## Team: <name>` section as it is unless the person asks you to change it.
- **Frontmatter:** `name: <type>`, a `description` under 200 characters saying what it covers and when to load it, and the label. Write the description as a folded block (`description: >-` and the text on the next line, indented): a colon in a plain one-line value makes the frontmatter invalid YAML, and the skill does not load.

  ```yaml
  ---
  name: dynatrace
  description: >-
    Acme's Dynatrace (SaaS + Grail): management zones, key services' entity ids, metric keys and log fields. Load it before you query Dynatrace.
  labels:
    - integration: dynatrace
  ---
  ```

- **Body:** a line on what is connected (each connection's name and what it reaches); where things live, under the customer's own names; the queries, filters and commands that ran, with what each is for; and pitfalls with what to do instead. Use the reference's "Capture" list as the checklist.
- **Code hosts** (GitHub, GitLab, Bitbucket, Azure DevOps): add a `## Repositories` section with a few lines on each repository the person selected: what it is, its main language, and where its deploy or production config lives.
- **Teams:** a `## Team: <name>` section holds what one team or domain needs on top of the rest (their services, dashboards, channels, conventions). Add one only when the person gives you that team's facts.
- **Write for the agents that read it.** Name the integration's own tools and CLIs (`dynatrace_query_logs`, `az pipelines runs list`), never your tools or `project_id`. Keep it to a page or two of stable facts: no live inventory the agents can list themselves, nothing that is true for every customer of the integration (a query language's syntax, a CLI's flags), except a guardrail that stops a call from failing.
- Never write a secret, token or password into the skill or the form, even one a tool returned.

## 7. End the turn

Say what you added to the form and to the skill, and from where; what you could not reach and why; and what the person should confirm. When the commit landed, give its commit. Then ask with `ask_user_input` what to do next, such as setting up another connected integration.
