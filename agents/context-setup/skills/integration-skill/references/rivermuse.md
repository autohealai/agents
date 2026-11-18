# RiverMuse

RiverMuse (RightITnow ECM) is a self-hosted event-correlation console: upstream monitors send it events, and it correlates them into the alerts on-call works from. What the RiverMuse skill must tell agents is this instance's own vocabulary: its saved filters, entity groups, connectors and custom fields.

## Capture

- **Scale and clock:** the active alert count from `rivermuse_test_connection`, and the configured server timezone, checked against the newest alert's `lastOccurence`.
- **Saved filters:** the saved alert filters teams work from, by exact name, with what each returns (`EMEA-Payments-Critical`: about 40 open, MAJOR and CRITICAL, entity group `EMEA-Payments`, from SolarWinds). Agents run them with `saved_filter`.
- **Entity groups:** which groups map to which services, sites or teams (`EMEA-Payments` = payments platform, Payments SRE).
- **Connector sources:** each `connectorSource` and the tool behind it (`SolarWinds` = network; `SCOM` = Windows hosts), and the Autoheal integration agents check next for that signal.
- **Custom fields:** each `customFields` key that matters, an example value, and whether it is numeric or text (`app_id`: text, internal application code; `cpu_events_counter`: numeric).
- **Event tokens:** the `tokens` keys each connector fills on raw events (`entity`, `message`), so agents know where the original message text is.
- **Environments:** how an alert shows its environment: an entity-group naming convention, `serviceTags`, or a custom field.
- **Ownership:** the `assignedUserGroup` and `owner` values and the teams behind them.
- **Filters that ran:** each filter tree written into the skill, with the `total_count` it returned.

## Ask the person

- Which saved filters does each team watch, and which are disaster-recovery views or unused?
- Which entity groups are production, and which team owns each?
- Which connector sources or alerts are known noise?

## Explore

- `rivermuse_test_connection` first. A 401 is the username or REST API token; a 403 is the ECM role missing the Alerts Console Tab or REST API permission. Stop and report either.
- Saved filters: `rivermuse_list_alert_filters`, then `rivermuse_search_alerts` with `saved_filter=<name>` and `max=5` on each likely one; note `total_count` and the dominant severity, entity group and connector.
- Vocabulary: `rivermuse_search_alerts` with `max=50` (newest first) for `entityGroups`, `connectorSource`, `serviceTags`, `assignedUserGroup` and the `customFields` keys.
- Filter test: every filter tree you will write, with `max=5`, such as `{"topOperator":"AND","nestedCriteria":[{"fieldName":"SEVERITY","fieldOperator":"GREATER_THAN","fieldValue":"MINOR"},{"fieldName":"ENTITY_GROUP","fieldOperator":"EQUALS","fieldValue":"EMEA-Payments"}]}`.
- Event trail: `rivermuse_list_alert_events` with the `alert_id` of one busy alert and `start=now-1d`, for its `tokens` keys.
- Roll-ups: `rivermuse_get_alert` with `include_nested=true` on an alert that has `hasNestedAlerts=true`.

## Guardrails

Write the ones agents will hit into the skill.

- Prefer `saved_filter` to a hand-written filter tree. A field this instance does not have returns an error, or an empty result that reads like "nothing is wrong"; ECM can also answer 404 when nothing matches.
- Filter operators are `EQUALS`, `NOT_NULL`, `CONTAINS`, `GREATER_THAN` and `LESS_THAN`. `SEVERITY` is ordered `CLEAR < INFO < WARNING < MINOR < MAJOR < CRITICAL`, so `GREATER_THAN MINOR` means MAJOR and CRITICAL. Numeric custom fields take `GREATER_THAN` / `LESS_THAN`; text ones take `EQUALS` / `CONTAINS`.
- Sort fields are spelled `FIRST_OCCURED` and `LAST_OCCURED`, with one R.
- `closed_alerts` differs by tool: on `rivermuse_search_alerts` it adds closed alerts to active ones; on `rivermuse_get_alert` it searches closed alerts only.
- `max` is at most 200. Read `total_count` to count; do not page to count.
- `rivermuse_list_alert_events` without `alert_id` sweeps every raw event in the window. Pass `alert_id`, or keep the window short; it may not exceed 31 days.
- Autoheal only reads ECM: it cannot acknowledge, assign, annotate or close alerts. Agents must not offer to.

## Pitfalls

- ECM timestamps carry no offset. When the newest `lastOccurence` is hours away from now, the integration's ECM Server Timezone setting is wrong: tell the person, and do not shift times by hand.
- Start from alerts, not events: events are the uncorrelated stream behind them.
- A saved filter that returns nothing may be a disaster-recovery or seasonal view. List it and say it was empty.
- In `saved_filters`, add each filter under its exact ECM name with what it returned in `agent_findings`; `description` and `selected` are the person's.
- `entity_groups`, `connector_sources`, `custom_fields` and `environments` are free text: write what the sampled alerts showed (`EMEA-Payments`: 120 of 500 sampled, from SolarWinds), so the person can correct it.

## Leave out

The ECM product model, the filter-tree grammar beyond the trees that ran, alert ids, and live alert counts per entity.
