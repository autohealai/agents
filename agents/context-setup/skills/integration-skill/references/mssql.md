# MS SQL Server

What the SQL Server skill must tell agents about this customer's database. Agents already know T-SQL and the catalog views; record what is true only here.

## Capture

- **Connection:** the database the connection opens, the edition and version (SQL Server 2019, Azure SQL Database), and the collation.
- **Tables:** each table agents use, schema-qualified (`app.ErrorLog`), what it holds, whether it is a log or event table or a state table, and its approximate row count.
- **Timestamps:** each table's time column and whether it holds UTC or server-local time (`app.ErrorLog.CreatedAt` is UTC: compare with `SYSUTCDATETIME()`). It is the most useful single fact here; decide it from sample rows.
- **Key columns:** status, level or error-code columns with their actual values (`Severity`: `INFO`, `WARN`, `ERROR`), ids that link to other systems (`OrderId`, `TraceId`), and columns whose meaning the name does not give.
- **Relationships:** the joins agents need (`dbo.Orders.CustomerId` to `dbo.Customers.Id`).
- **Quirks:** a case-sensitive collation (`*_CS_*`), JSON kept in `nvarchar` columns, large tables that need a tight time window.
- **DMV access:** whether the login can read `sys.dm_*` views (`VIEW SERVER STATE`, or `VIEW DATABASE STATE` on Azure SQL Database), and what agents use instead when it cannot.

## Ask the person

- Which tables do you query during an incident, and for what?
- Which status or error values mean customer impact?
- Which tables are too large to query without a tight time window?
- When samples do not settle it: does the application write timestamps in UTC or local time?

## Explore

- `mssql_test_connection` first, then `mssql_execute_query` with `SELECT DB_NAME() AS db, @@VERSION AS version, DATABASEPROPERTYEX(DB_NAME(), 'Collation') AS collation, SYSUTCDATETIME() AS utc_now, SYSDATETIME() AS local_now`.
- Tables: `SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_SCHEMA, TABLE_NAME`.
- Row counts without a scan: `SELECT TOP (50) s.name AS schema_name, t.name AS table_name, SUM(p.rows) AS approx_rows FROM sys.partitions p JOIN sys.tables t ON t.object_id = p.object_id JOIN sys.schemas s ON s.schema_id = t.schema_id WHERE p.index_id IN (0, 1) GROUP BY s.name, t.name ORDER BY approx_rows DESC`.
- Columns: `SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'Orders' ORDER BY ORDINAL_POSITION`.
- Samples: `SELECT TOP (5) * FROM dbo.Orders ORDER BY CreatedAt DESC`. Compare the newest `CreatedAt` with `utc_now` and `local_now` to tell UTC from local.
- Values: `SELECT TOP (20) Status, COUNT(*) AS cnt FROM dbo.Orders WHERE CreatedAt >= DATEADD(DAY, -1, SYSUTCDATETIME()) GROUP BY Status ORDER BY cnt DESC`.
- DMV access: `SELECT HAS_PERMS_BY_NAME(NULL, NULL, 'VIEW SERVER STATE') AS server_state, HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'VIEW DATABASE STATE') AS db_state`.

## Guardrails

Write the ones agents will hit into the skill.

- `mssql_execute_query` runs one statement that starts with `SELECT` or `WITH`. Any `;` is rejected, a trailing one too, so nothing such as `SET NOCOUNT ON` can precede the query.
- `INSERT`, `UPDATE`, `DELETE`, `DROP`, `CREATE`, `ALTER`, `TRUNCATE`, `EXEC`, `EXECUTE`, `MERGE`, `GRANT`, `REVOKE` and `DENY` are rejected anywhere after a space, even inside a string (`Message LIKE '% DELETE %'`). `SELECT ... INTO` is rejected.
- Stored procedures cannot run (`EXEC` is blocked): read `sys.*` and `INFORMATION_SCHEMA` views instead of `sp_who2` or `sp_helpindex`.
- `SET TRANSACTION ISOLATION LEVEL` cannot be sent. To read a busy table without waiting on locks, use the `WITH (NOLOCK)` table hint.

## Pitfalls

- On this form every column of `table_usage` and `useful_columns` is `both`: propose a `usage` or `description` line from what you found where the cell is blank.
- Write table names schema-qualified in the form and the skill (`dbo.Orders`): the same name can exist in two schemas.
- Filtering a UTC column against `GETDATE()` shifts the window by the server's offset. Record which clock each table uses.
- Case sensitivity comes from the collation, not the operator. Record the collation when it is case-sensitive.
- When DMV queries fail with "VIEW SERVER STATE permission was denied", write that into the skill and point agents at `sys.partitions`, `sys.tables` and `INFORMATION_SCHEMA`.

## Leave out

T-SQL syntax (`TOP` instead of `LIMIT`, `OFFSET ... FETCH`, date functions), general `NOLOCK` and collation explanations, the SQL Server error catalog, and examples that do not use this customer's tables.
