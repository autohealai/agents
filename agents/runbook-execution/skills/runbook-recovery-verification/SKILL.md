---
name: Verifying recovery after a runbook action
description: >-
  Decide whether a runbook action fixed what the alert was about, using the
  service's SLO signal over a fixed window rather than pod status, and what to
  do when it did not. Use before every runbook action and before resolving any
  incident a runbook action was meant to fix.
---

# Verifying recovery after a runbook action

> Written after a product-catalog restart brought all three pods back to Ready
> and the incident was resolved. /ListProducts was still failing 4% of
> requests: catalog-db was at its connection limit. The alert fired again 20
> minutes later and paged Storefront Squad with nothing but "resolved".

Pods Running and Ready says the restart finished. It does not say users are
being served. A readiness probe checks what it was written to check, and the
cause of an alert is often somewhere the probe does not look.

## 1. The tier gate

Read the service's tier from the service catalog before running anything.

| Action | tier-1 | tier-2, tier-3 |
|---|---|---|
| Delete one pod | pre-approved | pre-approved |
| Scale within the HPA's bounds | pre-approved | pre-approved |
| Rolling restart of a deployment | approval | pre-approved |
| Failover, rollback, anything else | approval | approval |

An action the table does not pre-approve waits for approval in Slack or the
UI. Ask with the evidence for the match and the check you will run after.

## 2. Name the recovery signal before acting

Take it from the service's SLO in the catalog: the error rate and p99 on the
SLO's endpoint. Add the alert's own condition: no new OOMKilled for an OOM, all
replicas available for a replica mismatch. Pull the same hour yesterday so you
know what normal looks like for this service at this time of day.

A runbook's own "done when" line is a floor, not the bar. Most of them were
written in terms of pods.

## 3. The window

- Starts when the rollout reports complete, not when the command was sent.
- Runs 15 minutes, in five 3-minute samples.
- **Recovered** when every sample is within the SLO, the alert's own condition
  holds, and nothing new fired in the alert group.

## 4. One attempt

If the window does not show recovery, do not run the action again. A second
restart that holds for 20 minutes hides the cause from the people who can fix
it, and costs them the 20 minutes.

## 5. Escalate with the action log

Escalate the incident to the owning team's on-call (PagerDuty level 2) and post
the same log in the team's channel:

- the alert, and the runbook it matched;
- each action, with its time and its result;
- the five samples, next to the SLO and the same hour yesterday;
- what still looks wrong, and the one thing you would check next.

## 6. After a recovery

Resolve the incident with the samples attached. If the runbook says the cause
is one the action only postpones, such as a leak, open a follow-up in Jira
project SHOP for the owning team, with the rate and the time the action bought.
