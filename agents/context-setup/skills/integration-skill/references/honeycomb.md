# Honeycomb

What the Honeycomb skill must tell agents about this customer's Honeycomb environment. Agents already know Honeycomb's query model and OpenTelemetry conventions; record what is true only here.

## Capture

- **Environment:** the Honeycomb team and environment each connection's key reaches (`acme` / `production`). A key reaches one environment only; another environment needs its own connection.
- **Datasets:** each dataset that matters, with its slug and what it holds (`checkout-api`: spans from the Checkout service; `k8s-events`: cluster events). Name the dormant ones, so agents skip them.
- **Service and environment columns:** the column that names a service (`service.name`) and, when one dataset holds several environments, the column and values that separate them (`deployment.environment` = `prod`).
- **Key columns per dataset:** route (`http.route`), status (`http.status_code` or `http.response.status_code`), error flag and message (`error`, `exception.message`), duration (`duration_ms`), and the column that identifies a customer (`app.tenant_id`). Write them per dataset when names differ.
- **Trace columns:** the trace and span id columns (`trace.trace_id`, `trace.parent_id`), and the datasets a trace crosses.
- **Boards:** the id and name of each board on-call opens, and what each shows.
- **Queries that ran:** the error-rate and latency queries for key services, as `honeycomb_run_query` arguments (`calculations=[{"op":"P99","column":"duration_ms"}]`, `filters=[{"column":"service.name","op":"=","value":"checkout"}]`, `breakdowns=["http.route"]`).

## Ask the person

- Which datasets and services matter most in an incident?
- Which column identifies a customer or tenant?
- What latency or error rate counts as bad for the key routes?

## Explore

- `honeycomb_test_connection` first: it returns the team and the environment of the key.
- Datasets: `honeycomb_list_datasets`, then `honeycomb_get_dataset` on the ones whose purpose is unclear.
- Columns: `honeycomb_list_columns` on each key dataset.
- Services and environments: `honeycomb_run_query` with `time_range=3600`, `breakdowns=["service.name"]` and `limit=20` on each key dataset; repeat with the environment column when there is one.
- Error and latency shape: `honeycomb_run_query` with `filters=[{"column":"error","op":"=","value":true}]` and `breakdowns=["service.name"]`, and with `calculations=[{"op":"P99","column":"duration_ms"}]` and `breakdowns=["http.route"]`.
- Boards: `honeycomb_list_boards`, then `honeycomb_get_board` on the ones on-call uses; their queries show the columns the team trusts.

## Guardrails

Write the ones agents will hit into the skill.

- `time_range` is seconds back from now, at most `604800` (7 days). The tool takes no start or end time, so query a range that covers the incident window.
- `calculations`, `filters` and `breakdowns` are JSON arrays: `[{"op":"COUNT"}]`, `[{"column":"service.name","op":"=","value":"checkout"}]`, `["http.route"]`. With no `calculations`, the query counts events.
- `honeycomb_run_query` waits about 15 seconds for the result. A result with `complete: false` did not finish: shorten `time_range`, or filter on a high-cardinality column (`trace.trace_id`, user ids) instead of breaking down by it.
- A 401 or 403 means the key is not an environment Configuration key with the Run Queries permission. Report it; do not retry.

## Pitfalls

- Column names often differ between datasets, for example older and newer OpenTelemetry status columns. Run `honeycomb_list_columns` on each dataset before you write a column into the skill.
- A filter on a column that does not exist in the dataset fails or returns nothing. Check the column against that dataset's list.
- In the `datasets` table, add rows with `name` only, set to the dataset slug. `description` and `selected` (Include) are the person's.
- `environments` takes the Honeycomb environment names, or the environment column's values when one dataset holds several.

## Leave out

Honeycomb's query operators, how heatmaps and BubbleUp work, OpenTelemetry semantic conventions in general, and examples that do not use this customer's datasets or columns.
