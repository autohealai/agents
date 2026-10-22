---
name: Attributing a post-deploy regression to the deploy
description: >-
  Decide whether a movement in error rate or latency after a deploy was caused
  by the deploy, or by something on a schedule, a dependency, or the traffic.
  Use after every production deploy before calling anything a regression.
---

# Attributing a post-deploy regression to the deploy

> Written after cart v4.2.1 was flagged as a regression and a revert was
> recommended. The bump was the 02:00 Redis snapshot, which produces the same
> error-rate step every night whether anything was deployed or not.

A pre/post comparison answers "did the numbers move?". It does not answer "did
the deploy move them?". Three checks do, and a regression is the deploy's only
when it clears all three.

## 1. The same hour last week

Pull the same 60-minute window from seven days earlier. If it shows the same
step, the movement is on a schedule: a nightly job, a snapshot, a batch, the
morning ramp. Name the schedule if you can find it; say "on a schedule" if you
cannot. Never call a regression on a movement last week also had.

## 2. Confined to the deployed service's own spans

Split the latency by span. A regression the deploy caused shows up in the
deployed service's own spans: the handler, the new call it makes, the query it
changed. If the time is spent in a downstream span instead, go to check 3.

## 3. The dependencies are flat

Read p99 and error rate for every service the deployed one calls, across the
same window. A degraded dependency makes every caller look regressed at once,
and reverting the caller fixes nothing.

## Severity

Use the SLO burn rate rather than the raw delta:

| Burn rate (1h window) | Meaning |
|---|---|
| below 2x | noise or a slow leak; report, do not page |
| 2x to 6x | real, page the owner during working hours |
| above 6x | page now; the monthly budget is gone in five days |

## What to do

- **All three checks pass:** page the owning team from the catalog with the
  evidence, and open a revert PR against the owning repository. The revert
  waits for the owner's approval.
- **Check 1 fails:** report it as a scheduled movement and name the schedule.
  Nothing to revert.
- **Check 2 or 3 fails:** report the dependency or span that moved. Nothing to
  revert in this service.
