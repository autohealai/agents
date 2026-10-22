---
name: Correlating alerts that fire together
description: >-
  Link alerts that fire within minutes of each other through the service
  dependency graph, find the service that caused them, and page its owner
  once. Also decides when a monitor is chronic noise and how to tune it. Use
  on every new alert group before paging anyone.
---

# Correlating alerts that fire together

> Written after currency was CPU-throttled at its 500m limit during the
> evening peak. checkout, frontend and cart alerted, and Checkout Squad was
> paged twice and Storefront Squad once. currency's only alert was info
> severity, so Payments Squad, who owned the cause, was not paged. It took 41
> minutes to hand the incident to them.

Grouping by service answers "which services are alerting?". It does not
answer "which service is the problem?". When several services alert within
minutes of each other they are usually one problem, and the services making
the most noise are the ones furthest from it.

## 1. Collect the window

Every alert that started within ten minutes either side of the new group,
from Datadog and from Alertmanager. Collapse the same monitor on several pods
or hosts into one line with a count. Keep the time each one first fired.

## 2. Link through the dependency graph

Read the service map for the window. Link two services' alerts when one calls
the other and the edge between them slowed or started failing in the window.
The callee usually fires first and its callers after it, nearest caller
first.

An alert on a service or node group with no edge to the others is its own
group. Do not fold it in because it fired in the same minutes.

## 3. Find the cause

Follow the slow edges to where they end. The cause is the service that is
unhealthy on its own terms:

| Signal on the service | Reading |
|---|---|
| CPU throttled, pool exhausted, its own spans slow | the cause |
| slow only in its calls to another service | a caller: waiting, not broken |
| latency flat, request rate up | taking retries: link it, do not blame it |

Then find what changed on the cause in the last 24 hours: a rollout, a Helm
values change, a resource limit, a flag. A values change ships with the same
image tag, so read the rollout history and the resources, not only the
version.

## 4. Route once

Page the owner of the cause, from the catalog, once, with every linked alert
attached. Add the owners of the linked services as subscribers: notified, not
paged. A group that arrives while a triage covering its window is open
attaches to that incident instead of paging again. A replay of a group that
has already resolved pages as a dry run.

## 5. Chronic noise

Read thirty days of history for every monitor in the window. A monitor is
chronic noise when all three hold:

| Test | Bar |
|---|---|
| Fires | 10 or more in 30 days |
| Resolves on its own | at least 9 in 10 |
| Acknowledged | never |

Propose a tuning that removes the benign fires and keeps the real fault
paging: a threshold above the highest benign peak, an evaluation window longer
than the benign excursion, or both. Backtest it against the thirty days and
say how many of the fires it would still have raised.

Do not mute. A muted monitor also misses the fault it was written for. Do not
tune a monitor that caught a real incident in the last 90 days.

The change is a write. It waits for the monitor owner's approval.
