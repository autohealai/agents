# Datadog

What the Datadog skill must tell agents about this customer's organization. Agents already know Datadog's search and metric query syntax and its logs, APM and monitor model; record what is true only here.

## Capture

- **Data the customer uses:** of Logs, APM, Infrastructure, Monitors, Incidents, Dashboards, SLOs and Synthetics, the ones they rely on. Name the empty ones, so agents do not search them.
- **Environment and service tags:** the tag that means "an environment" and its values, per product, since they often differ (`env:prod` on APM, `env:production` on logs, `kube_namespace:prod` on containers). The same for the service tag (`service:checkout-api`, or `kube_deployment:checkout` on containers).
- **Key services:** each important service's APM name, its environment value and its owner team (Checkout: `checkout-api` in `env:prod`, team `payments`).
- **Log fields:** the facets that matter, with the `@` prefix where they are attributes (`@http.status_code`, `@error.kind`, `@usr.id`), and the field that links a log to its trace.
- **Metrics:** the custom metrics they watch, what each means, and a query that ran (`sum:checkout.orders.failed{env:prod}.as_count()` is failed orders).
- **Monitors:** the naming and priority convention (`[P1]` title prefix, `priority:p1` tag), and the tags that route a monitor to a team.
- **Dashboards, SLOs, Synthetics:** the id and title of each key service's main dashboard; the name, id and target of each SLO that matters; the `public_id` and name of each test on a critical path.
- **Deployments:** how a deploy shows up: events from a source (`sources=github`), or the APM `version` tag.
- **Incidents:** the severity levels and the teams that handle them, when they use Datadog Incidents.

## Ask the person

- Which services matter most in an incident, and which `env` value is production?
- Which monitors or SLOs mean customer impact, and which monitors are known noise?
- Which teams own which services and monitors?
- What p99 latency counts as slow for the key services?

## Explore

- `datadog_test_connection` first: it checks the API key and the application key.
- Services and environments: `datadog_list_apm_services` with `env=*` over the last hour; owners from `datadog_list_service_catalog` and `datadog_list_teams`.
- Log tags: `datadog_get_log_volume` with `query=status:error` and `group_by=service`, then `group_by=env`, over the last hour. Then `datadog_search_logs` with `query=service:<service> status:error` and `limit=5` to read the attributes.
- Hosts and containers: `datadog_list_hosts` with `filter=env:<value>` and `count=5`; `datadog_get_host_tags` on one host; `datadog_search_containers` with `filter=kube_namespace:<ns>` and `page_size=5`.
- Monitors: `datadog_list_monitors` with `page_size=50`, and with `group_states=alert,warn` for what fires now.
- Dashboards with `datadog_list_dashboards` (`count=100`); SLOs with `datadog_list_slos` (`query=env:<value>`, `limit=20`); tests with `datadog_list_synthetic_tests`; incidents with `datadog_list_incidents` (`page_size=20`).
- Deploys: `datadog_search_events` over the last day with `tags=env:<value>`.
- Custom metrics: take a metric prefix from a dashboard or monitor query, list it with `datadog_list_metrics` (`filter=checkout`), and check one with `datadog_query_metrics`.

## Guardrails

Write the ones agents will hit into the skill.

- `datadog_search_logs` rejects an empty or `*`-only query. Its `limit` is at most 100.
- `datadog_list_hosts`, `datadog_search_containers`, `datadog_list_metrics` and `datadog_list_slos` require a filter, and truncate a broad response. Host, container and SLO pages hold at most 50.
- `datadog_list_apm_services`, `datadog_get_service_stats` and `datadog_get_service_dependencies` require `env` (`*` for all), `start` and `end`.
- Time formats differ by tool. `datadog_search_logs` takes `now-1h` or ISO8601. The other log tools and `datadog_search_traces` take ISO8601 or epoch milliseconds. The metric, APM service, event, monitor-history and SLO-history tools take Unix seconds. `datadog_get_synthetic_test_results` takes epoch milliseconds.
- `datadog_mute_monitor`, `datadog_unmute_monitor`, `datadog_create_incident` and `datadog_update_incident` change Datadog. Never call them while you set up.

## Pitfalls

- A fresh form lists every feature unselected: that is "none selected", not "no features". Probe each product and note in each row's `agent_findings` whether it has data.
- In logs, a tag (`env:prod`) and an attribute (`@env:prod`) are different filters. Write the one that returned data.
- The filter dropdowns (`logs_filter_env`, `logs_filter_service`, `apm_filter_env`, `infra_service_tag`, `infra_env_tag`) take patterns with placeholders as options (`env:<ENV>`, `service:<SERVICE>`, `kube_namespace:<ENV>`); the person picks. `logs_environments` takes the values (`production, staging`).
- In the tables, fill only the `both` columns: `field_name` and `sample_values` in `logs_useful_fields`, `name` and `target` in `slos_important`, and `name` in `apm_services`, `dashboards_useful` and `synthetics_critical`. The `description` columns are the person's.
- `apm_slow_threshold` and the monitor and incident fields are the person's. Put what you found (title prefixes, priority tags, incident severities) in that feature's `agent_findings`.

## Leave out

Datadog's log search and metric query syntax, `as_count()` and `as_rate()` rules, what standard facets such as `status` or `host` mean, and examples that do not use this customer's tags, services or metrics.
