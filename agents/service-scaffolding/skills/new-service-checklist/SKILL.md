---
name: Checklist for a new service
description: >-
  The six things a new service must have before it is handed to its team, one
  per new-service scorecard rule, where each value comes from, and how to check it
  once the repository exists. Use before creating a repository from a template,
  and when bringing an existing scaffold up to the checklist.
---

# Checklist for a new service

> Written after refunds and address-validation were created from go-service
> v3.2.0 and handed over with green CI. Both failed the scorecard on their
> first day. Eleven days later address-validation was still at one of six,
> with nobody named as its owner and nobody paged for it.

The template renders whatever it is given. A question nobody answers renders
as its default, and five of the six defaults fail a scorecard rule. A scaffold
is finished when all six items below hold a real value, not when CI is green.

## The six items

| # | Scorecard rule | What the repository must contain | Where the value comes from |
|---|---|---|---|
| 1 | CI | `.github/workflows/ci.yaml`, required on `main`, first run green | the template |
| 2 | Sized deployment | requests and limits on every container in `deploy/helm/values.yaml` | measured usage |
| 3 | Monitors and SLO as code | `ops/datadog/`: four monitors and one SLO | the service's interface |
| 4 | Pager | `ops/pagerduty.tf`: a service on the owning team's escalation policy | the owning team |
| 5 | Catalog entry | `catalog-info.yaml` with `owner` (a team) and `tier` | the request, else the platform's defaults |
| 6 | CODEOWNERS | `*` and the owning team's GitHub team | the owning team |

## Filling the values

- **Owner.** A team in the catalog, never a person and never TODO.
- **Tier.** As the request states, else the platform's default. Never raise a
  tier on your own; ask.
- **Requests and limits.** From measured p95 per pod: the service's own if it
  has run for a week, otherwise the closest service of the same language and
  shape. Requests at p95 rounded up to the next 50m CPU and 64Mi memory.
  Memory limit at twice the request; CPU limit 500m unless the reference has
  peaked above it.
- **Monitors.** Four, tagged `service:<name>`, notifying the team's PagerDuty
  service and Slack channel: error rate, the main operation's p99 (consumer
  lag for a consumer), one saturation signal, and pod restarts.
- **SLO.** One, named `<service>-availability-and-latency`, on the operation
  the service exists for.
- **Pager.** A PagerDuty service attached to the team's existing escalation
  policy. Never a new policy.

If a value can be neither found nor defaulted, ask on the request and create
nothing. A TODO handed to the team stays a TODO.

## Before creating

1. Look the name up in the scorecard. If the repository exists, do not create
   another: score it against the six items and open one pull request that
   brings it to six of six.
2. Put the plan, every item with its value and its source, in the approval
   request. Creating a repository waits for Platform Engineering.

## After creating

Read each item back from the live system, not from the file that should
create it:

| Item | Read it from |
|---|---|
| CI | the first workflow run on `main` |
| Sized deployment | the pods in `<staging-namespace>` |
| Monitors and SLO | Datadog, by `service:<name>` |
| Pager | PagerDuty, the service and its escalation policy |
| Catalog entry, CODEOWNERS | the files on `main` |

## Older scaffolds

A repository whose `.copier-answers.yml` names an earlier major of the
template gets a `copier update` pull request, lowest tier first, one per run.
The owning team merges it.
