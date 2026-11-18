# Sentry

What the Sentry skill must tell agents about this customer's Sentry organization. Agents already know Sentry's search syntax and its issue and event model; record what is true only here.

## Capture

- **Organization:** the org slug each connection reaches (`acme`; on Sentry Cloud it is the host's subdomain, `acme.sentry.io`). Every tool needs it.
- **Key projects:** each project that matters, with its slug, platform, the service it is, and its owner team (`checkout-api`: Python, the Checkout backend, team `payments`).
- **Environments:** the environment names Sentry records, per project when they differ (`production` in `checkout-api`, `prod` in `web-frontend`).
- **Releases:** the release format per project (`checkout@2.3.0`, a git SHA, a build number), and the projects that send no releases.
- **Custom tags:** the tags they set and what each means (`tenant` = customer account id, `region`, `feature_flag`), and how a Sentry user maps to a customer (`user.id` = account id).
- **Logs:** whether they use Sentry Logs, and the attributes that matter when they do.
- **Stack trace quality:** the projects whose frames are minified or unsymbolicated (no source maps or debug files uploaded), so agents do not trust frame names there.
- **Known noise:** issues or error types agents should skip, by title or short ID.

## Ask the person

- Which projects back which services, and which environment is production?
- Which issues or error types are known noise?
- How does a Sentry user or tag map to one of your customers?

## Explore

- `sentry_test_connection` first, then `sentry_list_organizations` for the org slugs.
- Projects and owners: `sentry_list_projects` and `sentry_get_teams` with the `org_slug`.
- Tags, environments and releases: `sentry_list_events` with `project_slug` and `per_page=10` on each key project; read `environment`, `release` and custom tags from each event's tags.
- Top issues: `sentry_list_issues` with `project_slug`, `query=is:unresolved environment:<env>` and `per_page=25`.
- Release format: `sentry_get_releases` with `project_slug` and `per_page=10`.
- Stack trace quality: `sentry_get_event_by_id` on one recent error event per key project.
- Logs: `sentry_search_logs` with `statsPeriod=24h` and `limit=5`. An empty result means Sentry Logs is not in use.

## Guardrails

Write the ones agents will hit into the skill.

- Every tool needs `org_slug`. `sentry_list_events` and `sentry_get_event_by_id` also need `project_slug`.
- On the issue and event list tools, `statsPeriod` takes only `24h`, `14d` or empty, and it only adds stats to the response. Narrow the time window in `query` instead.
- `sentry_search_logs` requires `statsPeriod`: one of `1h`, `24h`, `7d`, `14d`, `30d`. Its `limit` is 1 to 100.
- `sentry_list_issues` with no `query` returns only unresolved issues. Put another status in `query` (`is:resolved`) to see others.
- Pages hold at most 100 (`per_page`); page with `cursor`.
- `sentry_add_comment` writes to Sentry. Never call it while you set up.

## Pitfalls

- Some tools are aliases of others: `sentry_get_issues` and `sentry_list_issues`, `sentry_get_events` and `sentry_list_events`, `sentry_get_projects` and `sentry_list_projects`, `sentry_get_logs` and `sentry_search_logs`. Write one name of each pair in the skill.
- An environment filter that returns nothing often means the project spells it differently. Check the events' tags before you write the value.
- In the `projects` table, add rows with `name` only, set to the project slug. `description` and `selected` (Include) are the person's.
- `environments` takes the names Sentry records, comma-separated (`production, staging`), not names you expect.

## Leave out

Sentry search syntax (`is:unresolved`, `level:error`, `firstSeen:`), what issues, events and releases are, and examples that do not use this customer's projects, environments or tags.
