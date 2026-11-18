# ClickHouse

What the ClickHouse skill must tell agents about this customer's ClickHouse. Agents already know ClickHouse SQL and its functions; record what is true only here.

## Capture

- **Connection:** the connection's default database, the server version and the server time zone.
- **Tables:** each table agents use, with its database (`logs.app_logs`), what it holds, its engine, and its rough size in rows and bytes.
- **Time and keys:** each large table's time column, partition key and sorting key (`PARTITION BY toDate(timestamp)`, `ORDER BY (service, timestamp)`). Agents filter on these to avoid full scans.
- **Retention:** each table's TTL, or the oldest partition still present (`logs.app_logs` keeps 30 days).
- **Clusters:** on a sharded cluster, the `Distributed` table agents query (`logs.app_logs`) and the shard-local table behind it (`logs.app_logs_local`).
- **Rollups:** materialized views and pre-aggregated tables agents should prefer over raw rows (`metrics.requests_1m`), and what each aggregates.
- **Environment and service columns:** the column for each and its values (`env`: `prod`, `staging`; `service_name`: `checkout`, `payments`).
- **Key columns:** level or status columns with their exact values (`level`: `Error`, `Warning`), durations with units (`duration_ms`), ids that link to other systems (`trace_id`, `request_id`), and `Map` or `Nested` columns with the keys agents read (`attributes['http.status_code']`).
- **Time zone of the data:** whether `DateTime` columns hold UTC or carry their own zone (`DateTime('UTC')`, `DateTime64(3, 'Asia/Kolkata')`).

## Ask the person

- Which tables do you query during an incident, and for what?
- Which services and environments matter most, and what are they called in the data?
- Which rollup tables should agents use first, and which tables are too large to scan?
- Which errors or status values are known noise?

## Explore

- `clickhouse_test_connection` first, then `clickhouse_execute_query` with `SELECT version(), currentDatabase(), timezone() FORMAT JSON`.
- Tables: `SELECT database, name, engine, total_rows, formatReadableSize(total_bytes) AS size FROM system.tables WHERE database NOT IN ('system', 'INFORMATION_SCHEMA', 'information_schema') ORDER BY total_bytes DESC LIMIT 50 FORMAT JSON`.
- Keys, TTL and the `Distributed` target: `SELECT partition_key, sorting_key, engine_full FROM system.tables WHERE database = '<db>' AND name = '<table>' FORMAT JSON`.
- Columns: `SELECT name, type, comment FROM system.columns WHERE database = '<db>' AND table = '<table>' FORMAT JSON`.
- Data range without a scan: `SELECT min(partition), max(partition), sum(rows) FROM system.parts WHERE database = '<db>' AND table = '<table>' AND active FORMAT JSON`.
- Values: `SELECT env, count() AS n FROM <db>.<table> WHERE timestamp > now() - INTERVAL 1 HOUR GROUP BY env ORDER BY n DESC LIMIT 20 FORMAT JSON`, and the same for the service and level columns.

## Guardrails

Write the ones agents will hit into the skill.

- `clickhouse_execute_query` does not block writes: it runs whatever the connection's user may run. Send only `SELECT`, `SHOW`, `DESCRIBE` and `EXISTS`; never `INSERT`, `ALTER`, `OPTIMIZE`, `TRUNCATE`, `DROP` or `SYSTEM`.
- End each query with `FORMAT JSON`. Without it ClickHouse returns tab-separated rows with no column names.
- Name tables with their database (`logs.app_logs`) or pass `database`; otherwise the query runs in the connection's default database.
- Filter every query on the table's time column and add `LIMIT`. A scan of a large table runs until the 5-minute call limit.

## Pitfalls

- In `table_usage` and `useful_columns`, the `usage` and `description` columns are the person's: fill `table_name` and `column_name` (`app_logs.level`) only, and write what you learned about each into the skill.
- `total_rows` is empty for views and `Distributed` tables. Size them from the `MergeTree` table behind them.
- A shard-local table holds one shard's rows, so counts from it look low. Query the `Distributed` table.
- Names and string comparisons are case-sensitive: `level = 'error'` misses `Error`. Record exact values.

## Leave out

ClickHouse SQL and its functions (`quantile`, `toStartOfInterval`, `PREWHERE`, `LIMIT BY`), MergeTree internals, join advice, and examples that do not use this customer's tables or columns.
