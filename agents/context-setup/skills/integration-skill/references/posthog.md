# PostHog

What the PostHog skill must tell agents about this customer's PostHog organization. Agents reach PostHog only through `posthog-cli api` in the project's machine, and already know HogQL and the CLI; record what is true only here.

## Capture

- **Version property:** the exact event property that carries the release and its value format (`properties.release` = git SHA). PostHog has no standard name, so this matters most: without it agents cannot tie an incident to a deploy. When no event carries a version, say so.
- **Deploy markers:** whether they record deploys as annotations (and the text format, `Deploy checkout v2.3.0`) or as error-tracking Releases.
- **Environments:** how prod and staging are separated: separate projects, PostHog's Environments feature, or an event property, with its exact name and values (`properties.environment` = `production` / `staging`).
- **Projects:** each project id the agents should read and what it covers (`12345` = web app, prod; `12346` = web app, staging), and which one is the default.
- **Products in use:** of events, session replay, error tracking, feature flags, and insights and dashboards, the ones that hold data.
- **Customer mapping:** how a person maps to a customer (`distinct_id` = user email; person property `org_id` = account id).
- **Key events:** the custom events that mean user impact (`checkout_failed`, `payment_error`), and the properties on them that matter.
- **Queries that ran:** one `execute-sql` query per common question, written with this customer's properties (exceptions by `properties.release` in a time window).

## Ask the person

- Which property carries the release or version, and is the one you found the canonical one?
- Which project is production, and which product or service does each project cover?
- How does a PostHog person map to one of your customer accounts?

## Explore

- The first `bash` result names the host and the default project, if one is set.
- Tools: `posthog-cli api search <keyword>` finds read tools (`project`, `annotation`, `error`); `posthog-cli api info <tool>` shows a tool's arguments. Run `info` before each new `api call`.
- Schema: the `read-data-schema` tool for event names and properties, before any SQL.
- Version and environment: `posthog-cli api call execute-sql '{"query": "SELECT properties.$app_version, properties.release, properties.environment, count() FROM events WHERE timestamp > now() - INTERVAL 1 DAY GROUP BY 1, 2, 3 ORDER BY 4 DESC LIMIT 20"}'`, with the candidate properties the schema showed.
- Key events: `execute-sql` with `SELECT event, count() FROM events WHERE timestamp > now() - INTERVAL 1 DAY GROUP BY event ORDER BY count() DESC LIMIT 30`.
- Products: one bounded call each to `annotations-list`, `query-error-tracking-issues-list`, `query-session-recordings-list` and `feature-flag-get-all`.
- Customer mapping: `execute-sql` over `persons` with `LIMIT 5`, to read the person properties.

## Guardrails

Write the ones agents will hit into the skill.

- Rate limits are organization-wide and shared with the customer's own team. Run a few bounded queries: every query has a `timestamp` bound and a `LIMIT`.
- Check table and column names with `read-data-schema` before you write SQL; do not guess them.
- When there is no default project, pass the project id on every call.
- A 401 means the host and the key's region do not match. A 403 means a missing read scope (most often `user:read`, which the CLI needs before every call) or a key restricted to another project. Report it; do not retry.
- Run only read calls: queries, `list`, `get`, `search`. Never create, update or delete a PostHog resource.

## Pitfalls

- Do not assume `$app_version`. Many customers use a custom property; write the one that returned data.
- An environment filter that returns nothing may mean the environments are separate projects. Check the project map first.
- The five form fields are free text. Write property names exactly as HogQL reads them (`properties.release`), and mark what you inferred and the person has not confirmed.

## Leave out

HogQL syntax, `posthog-cli` usage beyond the guardrails, what each PostHog product is, and examples that do not use this customer's projects, properties or events.
