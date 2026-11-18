# OpenSearch

What the OpenSearch skill must tell agents about this customer's cluster. Agents already know the query DSL, PPL and SQL; record what is true only here.

## Capture

- **Deployment:** self-managed or an Amazon OpenSearch Service domain, the version, and the auth mode (basic, bearer, or AWS SigV4 through a linked AWS integration).
- **Query languages:** which of query DSL (`opensearch_search`), PPL and SQL (`opensearch_query`) work on this cluster. The SQL/PPL plugin can be disabled, so state it first.
- **Indices:** each index pattern that matters and what it holds (`logs-checkout-*` is Checkout's application logs, `otel-v1-apm-span-*` is traces), how it rotates (daily, rollover alias) and how far back it goes.
- **Environment filter:** the field that separates environments and its values (`kubernetes.namespace`: `checkout-prod`, `checkout-staging`), or the index naming that does it (`logs-prod-*`).
- **Service filter:** the field that names a service (`service.name`, `kubernetes.labels.app`) and the key services' names as they appear in it.
- **Exact filter fields:** for each field agents filter or aggregate on, the name to use, with `.keyword` where the mapping needs it (`kubernetes.labels.app.keyword`).
- **Log fields:** the timestamp field (`@timestamp`), the level field and its exact values (`level`: `ERROR`, `WARN`), the message field, and ids that link to other systems (`traceId`, `request_id`).
- **Per-index differences:** when indices name the same thing differently (`service.name` in `logs-app-*`, `app` in `legacy-*`), each index's field.

## Ask the person

- Which indices hold production logs, and which are archives or noise?
- Which services matter most in an incident, and what are they called in the logs?
- How long do they keep each index (retention or ISM policy)?
- Which errors or log lines are known noise?

## Explore

- `opensearch_test_connection` first: it reports the cluster, version and auth mode, and warns when the endpoint is not OpenSearch.
- Indices: `opensearch_list_indices` with `index_pattern` `*` gives names, health, status and document counts. Skip internal indices (`.opensearch-*`, `.kibana*`, `.opendistro-*`, `.plugins-*`).
- Fields: `opensearch_get_mappings` on an index or pattern; a pattern returns the mapping of the last matching index by name, the newest for date-suffixed indices.
- Environment and service values: `opensearch_search` with `query_body` `{"size":0,"query":{"range":{"@timestamp":{"gte":"now-24h"}}},"aggs":{"v":{"terms":{"field":"<field>","size":20}}}}`.
- Sample documents: `opensearch_search` with `"size":3`, the same `@timestamp` range and `"sort":[{"@timestamp":"desc"}]`.
- PPL and SQL: `opensearch_query` with `source=<index> | where level = 'ERROR' | stats count() by service.name | head 20`, then the same with `language` `sql` and `SELECT ... LIMIT 20`. Note which work.

## Guardrails

Write the ones agents will hit into the skill.

- `opensearch_query` needs the SQL/PPL plugin. When it returns a plugin error, use `opensearch_search`, which always works.
- `opensearch_query` takes `language` `ppl` (the default) or `sql`, nothing else. PPL starts with `source=<index>`; SQL uses `FROM <index>`.
- Responses over 10 MB fail with a "narrow the query" error, not partial data: cap `size`, `head` or `LIMIT`, project fields with `fields` or `_source`, and tighten the time range.
- Every query carries a time range on `@timestamp` and a `size`, `head` or `LIMIT`.
- With AWS SigV4, a credentials error means the linked AWS integration is inactive or its role cannot be assumed. Fix that integration; retrying does not help.

## Pitfalls

- The environment and service dropdowns (`log_filter_env`, `log_filter_service`) take field patterns with placeholders as options: `kubernetes.namespace:<ENV>`, `service.name:<SERVICE>`. Never add a value such as `environment:production`; the person picks the option.
- `environments` is a comma-separated list of the environment values you saw (`production, staging`).
- In `useful_fields`, fill `field_name` and `sample_values` from real aggregations; `description` is the person's.
- `keyword` fields match exactly, case included: `level: "error"` returns nothing when the data says `ERROR`. Check the values before you write a filter.
- When `opensearch_test_connection` warns that the endpoint is Elasticsearch, stop and tell the person to connect it with the Elasticsearch integration instead.

## Leave out

Query DSL, PPL and SQL syntax, how mappings and ISM work in general, and examples that do not use this customer's indices or fields.
