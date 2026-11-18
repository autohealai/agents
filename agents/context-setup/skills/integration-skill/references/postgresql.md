# PostgreSQL

What the PostgreSQL skill must tell agents about this customer's database. Agents already know PostgreSQL SQL and its catalog views; record what is true only here.

## Capture

- **Connection:** the database each connection opens, the server version, and where it runs (RDS, Cloud SQL, self-hosted) when the person says. Each connection reaches one database; with several databases, say which connection holds which.
- **Tables:** each table agents use, schema-qualified (`billing.invoices`), what it holds, whether it is a log or event table or a state table, and its approximate row count.
- **Timestamps:** each table's time column, its type (`timestamptz`, or `timestamp` without a zone) and, for `timestamp`, the zone the application writes. Note whether the column is indexed: an unindexed time filter on a large table scans it.
- **Partitioned tables:** the parent agents query (`events`) and how it is split (monthly by `created_at`).
- **Key columns:** status or error columns with their actual values (`status`: `pending`, `failed`), ids that link to other systems (`order_id`, `trace_id`), enum types with their labels, and `jsonb` columns with the keys agents read (`payload->>'error_code'`).
- **Quoted names:** tables or columns created with capitals (`"OrderItems"`, `"createdAt"`) that agents must quote every time.
- **Relationships:** the joins agents need (`orders.customer_id` to `customers.id`).
- **Stats access:** whether the login sees other sessions' queries in `pg_stat_activity`. It needs `pg_read_all_stats`; without it `query` shows `<insufficient privilege>`.

## Ask the person

- Which tables do you query during an incident, and for what?
- Which status or error values mean customer impact?
- Which tables are too large to query without a tight time window?
- When samples do not settle it: does the application write `timestamp` columns in UTC?

## Explore

- `postgresql_test_connection` first, then `postgresql_execute_query` with `SELECT current_database(), version(), current_setting('TimeZone')`.
- Tables by size: `SELECT schemaname, relname, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC LIMIT 50`.
- Columns: `SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'orders' ORDER BY ordinal_position`.
- Indexes: `SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'public' AND tablename = 'orders'`.
- Partitions: `SELECT p.relname AS parent, c.relname AS part FROM pg_inherits i JOIN pg_class p ON p.oid = i.inhparent JOIN pg_class c ON c.oid = i.inhrelid ORDER BY 1, 2 LIMIT 100`.
- Samples and values: `SELECT * FROM public.orders ORDER BY created_at DESC LIMIT 5`; `SELECT status, count(*) FROM public.orders WHERE created_at > now() - interval '1 day' GROUP BY status ORDER BY 2 DESC LIMIT 20`.
- Stats access: `SELECT pg_has_role(current_user, 'pg_read_all_stats', 'member')`.

## Guardrails

Write the ones agents will hit into the skill.

- `postgresql_execute_query` runs one statement that starts with `SELECT` or `WITH`. A trailing `;` is fine; any other `;` is rejected.
- `EXPLAIN`, `SHOW` and `SET` are rejected. Read a setting with `SELECT current_setting('<name>')`.
- `INSERT`, `UPDATE`, `DELETE`, `DROP`, `CREATE`, `ALTER`, `TRUNCATE`, `EXEC`, `MERGE`, `GRANT`, `REVOKE` and `DENY` are rejected anywhere after a space, even inside a string (`query ILIKE '% UPDATE %'` on `pg_stat_activity`). `SELECT ... INTO` is rejected.
- Bound every query by a time filter on an indexed column and a `LIMIT`. A call stops after 5 minutes.

## Pitfalls

- In `table_usage` and `useful_columns`, the `usage` and `description` columns are the person's: fill `table_name` and `column_name` (`orders.status`) only, and write what you learned about each into the skill.
- Unquoted names fold to lowercase: `SELECT * FROM OrderItems` fails when the table is `"OrderItems"`. Write such names with their quotes.
- `n_live_tup` is an estimate, and a partitioned parent holds no rows itself. Size a partitioned table from its partitions.
- A `timestamp` column compared with `now()` is read in the session's `TimeZone`. Record the zone the data is in.

## Leave out

PostgreSQL syntax (`ILIKE`, `::` casts, `interval`, `date_trunc`), the catalog and `pg_stat_*` views in general, query-plan advice, and examples that do not use this customer's tables.
