---
name: Proposing an SLO from the service's own history
description: >-
  Derive the SLI, the latency threshold and the target from 28 days of a
  service's real traffic, so the SLO is one the service already meets. Use
  whenever a scorecard sweep finds a service with no SLO, or one nobody meets.
---

# Proposing an SLO from the service's own history

> Written after the week-38 sweep proposed 99.99% availability and a 150ms p99 for shipping. shipping had not reached either on any of the previous 28 days, and the ticket carrying the proposal sat for two weeks with nobody assigned.

A target is a promise about the service as it is, not as a standard says it should be. A target the service has never met pages on its first day, and a page nobody believes is worse than none. Start from what it did.

## 1. The SLI

Take the customer-facing endpoint with the most traffic. A request is good when it is not a 5xx AND it finishes under the latency threshold. One SLI that covers both is easier to own than two.

## 2. The latency threshold

Take the worst daily p99 over the last 28 days, multiply it by 1.3, and round UP to the next 50ms. The threshold sits above every ordinary day, so it counts the requests that were slow, not the usual tail.

## 3. The target

Compute the share of good requests in every rolling 7-day window across the 28 days. Take the WORST window and round it DOWN to a step:

| Worst 7-day window | Target |
|---|---|
| 99.95% or better | 99.95% |
| 99.9% to 99.95% | 99.9% |
| 99.5% to 99.9% | 99.5% |
| 99.0% to 99.5% | 99.0% |
| below 99.0% | no target yet; fix the worst week first |

Never propose a target above the 28-day level. Never cut an incident out of the history to reach a rounder number: it happened to the customers.

## 4. Check the budget

Budget = (1 − target) × the requests in 28 days. Compare it with the bad requests the service actually produced in the same 28 days:

- **40–80% of the budget spent:** propose the target.
- **More than 80%:** step the target down once. A service that spends most of its budget doing what it always does has no room for a bad deploy.
- **Less than 40%:** propose it anyway, and say it can tighten after the next 28 days.

## 5. The alerts

Two burn-rate monitors, on the same bands Deploy Verification uses:

- page the owning team above 6× burn over 1 hour, confirmed over 5 minutes;
- notify in working hours above 2× over 6 hours.

## What goes in the pull request

- `ops/datadog/slo.tf`: the SLO, named `<service>-availability-and-latency`, on a 28-day rolling window.
- `ops/datadog/monitors.tf`: the two burn-rate monitors, routed to the service's PagerDuty service.
- A table in the body: window, request count, 28-day level, worst 7-day window, worst daily p99, threshold, target, budget, and the share of the budget the service spends today.

Request review from the repository's CODEOWNERS team. The owners merge; the next sweep sees the SLO and closes the rule.
