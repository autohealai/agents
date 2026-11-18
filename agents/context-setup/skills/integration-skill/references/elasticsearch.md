# Elasticsearch

What the Elasticsearch skill must tell agents about this customer's cluster. Agents already know the query DSL and ES|QL; record what is true only here.

## Capture

- **Deployment:** self-managed, Elastic Cloud or Serverless, and the version. It decides whether `elasticsearch_esql` and `elasticsearch_get_shards` work, so state it first.
- **Indices:** each index pattern or data stream that matters and what it holds (`logs-checkout-*` is Checkout's application logs, `filebeat-*` is node logs), how it rotates (daily index, rollover data stream) and how far back it goes.
- **Environment filter:** the field that separates environments and its values (`kubernetes.namespace`: `checkout-prod`, `checkout-staging`), or the index naming that does it (`logs-prod-*`).
- **Service filter:** the field that names a service (`service.name`, `kubernetes.labels.app`) and the key services' names as they appear in it.
- **Exact filter fields:** for each field agents filter or aggregate on, the name to use, with `.keyword` where the mapping needs it (`kubernetes.labels.app.keyword`).
- **Log fields:** the timestamp field (`@timestamp`), the level field and its exact values (`log.level`: `ERROR`, `WARN`), the message field, and ids that link to other systems (`trace.id`, `request_id`).
- **Per-index differences:** when indices name the same thing differently (`service.name` in `logs-app-*`, `app` in `legacy-*`), each index's field.

## Ask the person

- Which indices hold production logs, and which are archives or noise?
- Which services matter most in an incident, and what are they called in the logs?
- How long do they keep each index (retention or ILM policy)?
- Which errors or log lines are known noise?

## Explore

- `elasticsearch_test_connection` first: it reports the cluster name and health, or the version with "(Serverless)" on Serverless.
- Indices: `elasticsearch_list_indices` with `index_pattern` `*` gives names, status and document counts. Skip dot-prefixed system indices; a data stream's backing indices show as `.ds-<stream>-<date>-<n>`, so query the stream name.
- Fields: `elasticsearch_get_mappings` on one concrete index, the newest of each pattern.
- Environment and service values: `elasticsearch_search` on the index with `query_body` `{"size":0,"query":{"range":{"@timestamp":{"gte":"now-24h"}}},"aggs":{"v":{"terms":{"field":"<field>","size":20}}}}`.
- Sample documents: `elasticsearch_search` with `"size":3`, the same `@timestamp` range and `"sort":[{"@timestamp":"desc"}]`.
- ES|QL: `elasticsearch_esql` with `FROM <index> | WHERE @timestamp > NOW() - 1 hour | STATS count() BY log.level | LIMIT 20`. Note whether it works.

## Guardrails

Write the ones agents will hit into the skill.

- `elasticsearch_esql` needs Elasticsearch 8.11 or later. On an older cluster it fails: use `elasticsearch_search`.
- `elasticsearch_get_mappings` with a pattern returns the mapping of one matching index, not always the newest: pass a concrete index name.
- `elasticsearch_get_shards` reads `_cat/shards`, which Serverless does not offer.
- Do not pass `fields` to `elasticsearch_search`; put `"_source": ["<field>", ...]` inside `query_body`.
- Every search carries an `@timestamp` range and a `size`, and every ES|QL query a `WHERE` on time and a `LIMIT`. An unbounded search over `logs-*` runs into the 2-minute call limit.

## Pitfalls

- The environment and service dropdowns (`log_filter_env`, `log_filter_service`) take field patterns with placeholders as options: `kubernetes.namespace:<ENV>`, `service.name:<SERVICE>`. Never add a value such as `environment:production`; the person picks the option.
- `environments` is a comma-separated list of the environment values you saw (`production, staging`).
- In `useful_fields`, fill `field_name` and `sample_values` from real aggregations; `description` is the person's.
- `keyword` fields match exactly, case included: `log.level: "error"` returns nothing when the data says `ERROR`. Check the values before you write a filter.
- A field mapped as `text` cannot be aggregated or matched exactly; use its `.keyword` subfield when the mapping has one, and write that name into the skill.

## Leave out

Query DSL, ES|QL and Lucene syntax, how mappings, data streams and ILM work in general, and examples that do not use this customer's indices or fields.
