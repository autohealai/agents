---
name: Deciding what a green canary is evidence of
description: >-
  Work out which of a release's changed paths a canary actually exercised and
  which it never reached, before reading a green result as safety. Use whenever
  a canary is about to be treated as evidence that a release can ship.
---

# Deciding what a green canary is evidence of

> Synthesised from three releases between 2026-08-22 and 2026-09-04 whose
> canary was green and whose incident followed inside the day. In all three the
> canary was correct about the traffic it saw, and the traffic it saw did not
> include the path that broke.

A canary is evidence about **the paths it exercised, in the window it ran, at
the share it took**. It is not evidence about the release. Those are the same
sentence only when the release changes nothing outside that set, which is
rarer than it sounds.

## The question to ask

Not "was the canary green". For each changed path: **could this canary have
reached it at all?**

```
expected hits ≈ path's normal rate × canary traffic share × window length
```

Below about five expected hits, a green result is silence rather than evidence.
Compute it per path, not for the service.

## The four kinds of path a canary routinely misses

1. **Scheduled work.** Jobs, reconciliation passes, exports. A twenty-minute
   canary at 20:10 has not met the job that runs at 02:00, and the job is often
   the only remaining reader of whatever the release removed.
2. **Low-frequency endpoints.** Refunds, address changes, admin actions,
   anything a customer does once a quarter. Real traffic, far below the rate
   the arithmetic above needs.
3. **Conditioned paths.** Per-region, per-tenant, per-plan or per-locale code.
   A 5% canary in one region is 0% of the other two.
4. **Anything behind a flag that is off in canary.** Which is most new code,
   and is the reason the canary was green.

## Saturation is a rate, and a share divides it

A canary takes a fraction of the traffic, so it takes the same fraction of
anything that accumulates — connections, pool slots, queue depth, lock
contention. A change that exhausts a resource at 100% of traffic will sit
comfortably inside it at 5% and report green.

The worked case this skill came from: `payment v2.14.0` raised its retry budget,
canaried at 5% for fifteen minutes, and went out green. At 5% the extra
attempts occupied a handful of `checkout`'s 64 pool slots. At 100% they took
all of them, seven minutes after the rollout finished.

## The rule of thumb that settles most of it

**A canary shorter than one full traffic cycle has not exercised the cyclical
work.** For this shop a cycle is twenty-four hours, because the reconciliation
and export jobs are nightly. If the release touches anything cyclical, either
run the canary across a cycle or run the cyclical job against the canary
explicitly — and say which you did.

## What a green canary does NOT tell you

- Not that the migration is reversible. Different question; see
  `migration-reversibility`.
- Not that the rollback works. A canary tests the way in.
- Not that the uncovered paths are fine. It tells you nothing at all about
  them, and the report should say so.
