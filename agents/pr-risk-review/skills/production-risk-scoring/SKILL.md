---
name: Scoring a pull request's production risk
description: >-
  Score a pull request's production risk from 0 to 100 from the catalog,
  incident history, live traffic and, for a migration, the real table, before
  reviewing the diff. Use on every pull request review.
---

# Scoring a pull request's production risk

> Written after payment#1529 was reviewed as "merge after nits". It raised
> the currency client's retries from 2 to 4 attempts. That is the change class
> of payment v2.14.0, which saturated checkout's gRPC pool and failed
> checkouts for 46 minutes. The diff was correct. The risk was not in the
> diff.

A diff tells you whether the code is right. It does not tell you what happens
to production when the code is right and something else goes wrong. Read
production first, score it, then review the diff.

## The score

| Component | Points | How to read it |
|---|---|---|
| Blast radius | 0–30 | Callers of what the PR changes, from the catalog. 25–30 when a purchase would fail; 10–24 when a page or a purchase step degrades; under 10 when only an error message or a log changes. |
| Tier | 0–25 | tier-1 25, tier-2 12, anything else 5. |
| Incident history | 0–25 | 25 when an incident in the last 90 days was caused by this change class in these files; 10–20 when the class matches on the same call path; 0 when neither. |
| Change size and kind | 0–20 | 1 per 50 lines changed (up to 7), plus 8 for a migration on a table that takes writes, plus 5 for a timeout, retry or pool setting. |

| Score | Band | What the review does |
|---|---|---|
| 0–39 | low | The owning team reviews. |
| 40–69 | elevated | The owning team, and the owner of any other path the PR changes. |
| 70–100 | high | Both, and a canary recommendation: 5% for one peak hour. |

## Change classes that have caused incidents here

**Retry, backoff and deadline changes on a client.** Run the arithmetic
rather than judging by eye:

```
hold time    = attempts × (per-attempt deadline + backoff)
slots needed = calls/s at the peak × hold time
```

Compare it with the caller's pool. checkout's gRPC pool to payment has 64
slots. A policy that needs more than the pool when the dependency stalls is
the v2.14.0 class, however small the diff is. Read Sentry before you accept
the reason for a longer deadline: errors that cluster in a dependency's slow
windows are the dependency's problem, and a longer deadline turns them into
held slots.

**Migrations on a table that takes writes.** See below.

## Migrations

Read the table's live rows and its writes per second at the peak from
Datadog: `postgresql.live_rows`, `postgresql.rows_inserted`,
`postgresql.rows_updated`. Then read the lock the statement takes:

| Statement | Lock on the table | Blocks |
|---|---|---|
| `CREATE INDEX` | SHARE | INSERT, UPDATE and DELETE, for the whole build. Reads continue. |
| `CREATE INDEX CONCURRENTLY` | SHARE UPDATE EXCLUSIVE | Neither reads nor writes. Schema changes and VACUUM on the table wait. |
| `DROP INDEX` | ACCESS EXCLUSIVE | Everything, reads included, until the drop completes. |
| `ALTER TABLE` that changes a column's type | ACCESS EXCLUSIVE | Everything, and it may rewrite the table. |

- **Blocked writes ≈ writes/s at the peak × build time.** Use a measured
  build time where one exists, such as a migration check against a restored
  snapshot. That check passes whatever lock the statement takes, because
  nothing writes to the snapshot while it runs.
- **Each blocked write holds a database connection.** Once the blocked
  writes outnumber the service's pool, every query the service makes waits
  for a connection, reads included.
- **`CONCURRENTLY` cannot run inside a transaction block.** goose wraps each
  migration in one by default, so the statement goes in its own file marked
  `-- +goose NO TRANSACTION`. It scans the table twice and takes longer.
  If it fails, it leaves an INVALID index behind: drop it before retrying.

A statement that blocks writes on a table with sustained writes is a
blocking finding, whatever CI says.

## What the review says

The score and its four components first, each with the fact behind it. Then
the findings, ranked blocking, high and advisory, each with its file and line
and the production fact that sets its severity. Blocking means "merging this
as written breaks production", nothing less. When a migration finding is
blocking, post it to the owning team's channel: someone has to schedule the
fixed migration, and it may not be the PR's author.
