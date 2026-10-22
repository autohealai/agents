---
name: Deciding whether a migration can be rolled back
description: >-
  Separate a migration that can genuinely be undone from one that only looks
  undoable, and find whatever still reads what it removes. Use before approving
  any release that carries a schema change.
---

# Deciding whether a migration can be rolled back

Two questions, and they are independent. A migration can be perfectly
reversible and still take production down for as long as it is applied; a
migration can be irreversible and completely safe. Answer both.

## 1. Can it be undone?

A down migration that restores the **shape** is not a rollback if the **data**
is gone. Re-adding a dropped column gives you a column full of nulls, and the
rows that had values in it are not coming back from the schema.

Irreversible in practice, whatever the down migration claims:

- `DROP COLUMN` / `DROP TABLE` — the data is gone at commit.
- Narrowing a type (`text` → `varchar(32)`, `bigint` → `int`) — the truncated
  rows are gone even though the column survives.
- `ADD COLUMN NOT NULL` with a computed backfill — the down path drops the
  column, and the computation that filled it is not stored anywhere.
- Anything that rewrites rows in place. A down migration that recomputes is a
  second migration, not an undo.

Reversible: adding a nullable column, adding an index, adding a table, widening
a type, adding a default.

## 2. Is anything still reading it?

Search the **whole repository**, not the service that owns the table. Then
search the things that do not run on a request, because those are the ones a
release review misses — nothing exercises them while anybody is watching:

- scheduled jobs and reconciliation passes
- nightly and weekly exports
- admin and support tooling
- anything under a cron, a workflow definition or a Helm `CronJob`
- the previous release's code, which is still running during the rollout

That last one is the one people argue about. During a rolling deploy both
versions are live, so a migration that removes something the OLD code reads
breaks the old pods until they are gone — and if you then roll back, it breaks
the new ones for good.

## The shape that is almost always right

Expand and contract, across two releases:

```
release N     stop writing the column; keep reading it; migration adds nothing
release N+1   stop reading the column
release N+2   drop the column
```

Each step is reversible on its own. The version that ships all three at once is
the version that cannot be rolled back, and it is usually shipped that way
because the three felt like one change.

## What NOT to accept

- Not "the down migration exists" — read it, and ask what it restores.
- Not "nothing in this service reads it" — the reader is usually in another one.
- Not "the canary was green" — a canary that ran for twenty minutes has not met
  a job that runs at 02:00. That is a different check; see `canary-coverage`.
