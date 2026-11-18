# Grafana

What the Grafana skill must tell agents about this customer's Grafana instance. Agents already know PromQL, LogQL and LogsQL; record what is true only here.

## Capture

- **Data sources:** each Prometheus, Loki and VictoriaLogs data source the customer uses, with its name, type and UID (`prod-metrics`, `prometheus`, `PBFA97CFB590B2093`), and what it covers (one cluster, one region, every environment). Every query needs the UID.
- **Log backend:** Loki or VictoriaLogs, per log data source. The query language follows from it, so state it first.
- **Log scoping:** the label that means "an environment" and the one that means "a service", with their values (`{namespace="prod", app="checkout"}`). For VictoriaLogs, which are stream labels (`_stream:{namespace="prod"}`) and which are plain fields (`level:error`).
- **Log format:** JSON or logfmt per key service, the parser that works (`| json`), and the fields that matter (`level`, `status`, `trace_id`).
- **Metric scoping:** the labels for environment and service in Prometheus, which often differ from the log labels (`cluster="prod-eu"`, `job="checkout"`).
- **Key metrics:** the metrics they watch, what each means, and a query that ran (`sum(rate(http_server_requests_seconds_count{job="checkout", status=~"5.."}[5m]))` is the Checkout error rate).
- **Dashboards:** the title and UID of each key service's dashboard and of the on-call overview, with their template variables (`$namespace`, `$service`) and the values to use.
- **Alert rules:** the folders or rule groups per team, and the labels that carry severity and owner (`severity`, `team`).

## Ask the person

- Which services matter most in an incident, and which namespace, cluster or environment value is production?
- Which dashboards does on-call open first?
- Which metrics mean customer impact for them?
- Which alert rules are known noise?

## Explore

- `grafana_test_connection` first, then `grafana_list_datasources` for names, types and UIDs.
- Log labels: `grafana_logs_field_names` with the log `datasource_uid` over the last hour, then `grafana_logs_field_values` on the environment and service candidates (`namespace`, `env`, `app`, `service_name`).
- Log format: `grafana_query_logs` with a stream selector for one service and `limit=5`.
- Metric labels: `grafana_query_prometheus` instant queries, such as `count by (namespace) (up)` and `count by (job) (up{namespace="<ns>"})`.
- Dashboards: `grafana_list_dashboards` with `query` or `tag` and a `limit`, then `grafana_get_dashboard` on the top ones. Their panel queries name the metrics that matter. Run one panel query with `grafana_query_prometheus`, variables filled in.
- Alert rules: `grafana_list_alert_rules` with `limit=50`, then with `folder_uid` or `group_name` once you know them.

## Guardrails

Write the ones agents will hit into the skill.

- Every query tool needs a `datasource_uid` from `grafana_list_datasources`; a name or a guessed UID fails. `grafana_query_prometheus` needs the UID of a `prometheus` data source.
- The log tools work only on `loki` and `victoriametrics-logs-datasource` data sources. Pass `datasource_type` to skip detection.
- Never put `| limit N` in a LogQL or LogsQL query: use the `limit` parameter. A Loki query needs a stream selector.
- Log windows longer than 12 hours often hit the 30-second upstream timeout. Default to the last hour, and split a wider window into slices of 12 hours or less.
- `grafana_query_prometheus` runs a range query only when both `start` and `end` are set; otherwise it runs an instant query. Times take Unix seconds, RFC3339 or `now-1h` (units `s`, `m`, `h`, `d` only).
- Dashboard lists and log results are capped. Narrow with `query` or `tag`, page with `page`, and on truncation shorten the window or lower `limit`.

## Pitfalls

- A fresh form lists every feature unselected: that is "none selected", not "no features". Probe Logs, Metrics and Dashboards and note in each row's `agent_findings` whether they are reachable.
- In VictoriaLogs, only stream labels go inside `_stream:{}`. `_stream:{level="error"}` returns nothing when `level` is a plain field: write `level:error`.
- Dashboard panel queries contain template variables (`$namespace`, `${service}`, `$__rate_interval`). Replace them with real values before you write a query into the skill.
- The filter dropdowns (`logs_filter_env`, `logs_filter_service`, `metrics_filter_env`, `metrics_filter_service`) take patterns with placeholders as options: `{namespace="<ENV>"}` for Loki, `namespace:<ENV>` or `_stream:{namespace="<ENV>"}` for VictoriaLogs, `namespace="<ENV>"` for metrics. The person picks. `logs_environments` takes the values.
- In `metrics_key_metrics` and `dashboards_useful`, fill only the name column (`metric_name`, `name`). The `description` column is the person's.

## Leave out

PromQL, LogQL and LogsQL syntax, generic `rate()` and `histogram_quantile()` advice, and examples that do not use this customer's data sources, labels or metrics.
