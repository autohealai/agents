---
name: Attributing a cost anomaly to the change that caused it
description: >-
  Decide what made a cost line step: a configuration change, a deploy, a
  scaling event or traffic. Use on every Vantage anomaly alert before naming a
  cause, an owner or a fix.
---

# Attributing a cost anomaly to the change that caused it

> Written after the storefront node group's step was reported as traffic
> growth. Requests were flat. The group's minimum had been raised from 6 to 20
> by hand for a load test and never put back, and it ran at +$110 a day for ten
> days before anyone looked.

A line's trend answers "how much did it grow?". It does not answer "why?".
Traffic grows in slopes. Changes make steps. Four things make a cost line step,
and the report names one only after all four are lined up against the hour the
spend moved.

## 0. The hour, and the usage type

Vantage gives the day. Cost Explorer, grouped by usage type at hourly
granularity, gives the hour and says what is being metered: ingestion or
storage, instance hours or data transfer. Whatever you name as the cause has to
explain that usage type. A retention change cannot raise ingestion; a log level
cannot raise instance hours.

## 1. Configuration changes (CloudTrail)

Look up write events on the line's resources, from 24 hours before the step to
now. The usual ones:

| Change | CloudTrail event | Usage type that moves | What it looks like |
|---|---|---|---|
| Log level raised | `ssm:PutParameter` on a `LOG_LEVEL` | `DataProcessing-Bytes` | one service's log bytes step; requests flat |
| Node group minimum raised | `eks:UpdateNodegroupConfig` | `BoxUsage:<type>` | node count pinned at the minimum; CPU low |
| Auto Scaling group resized | `autoscaling:UpdateAutoScalingGroup` | `BoxUsage:<type>` | desired capacity flat at the new value |
| Lifecycle rule removed | `s3:PutBucketLifecycleConfiguration`, `s3:DeleteBucketLifecycle` | `TimedStorage-ByteHrs` | storage climbs instead of levelling off |
| Log retention raised | `logs:PutRetentionPolicy` | `TimedStorage-ByteHrs` | storage grows; ingestion flat |

Hand edits made during an incident or a load test are the first suspects. Look
for a later event that put the value back. No later event means it is still on.

## 2. Deploys (GitHub)

List production deploys of every service that writes to the resource, across
the same window. A deploy is ruled out when its time does not match the step
within the hour, or when its own service's share of the line did not move.

## 3. Scaling events

Node count, desired capacity and task count across the window. Scaling that
follows request rate is traffic. Capacity held up by a minimum is a change.

## 4. Traffic

Request rate at the edge over the same hours, against the same day the week
before. Traffic explains a step only when the usage moved by about the same
factor as requests, and the cost per request is flat.

## Naming the cause

Name a cause when all three hold:

1. its time matches the step to within the hour;
2. its mechanism explains the usage type that moved;
3. the other three candidates are ruled out, each with its evidence.

Otherwise return `unexplained` and say which of the three is missing.

## Owner, impact and fix

- **Owner:** the team that owns the service or resource in the catalog. Name
  the team, not the person who made the change.
- **Impact:** dollars per day, per month (30 days), and spent so far.
- **Fix:** when the resource is declared in code, open a pull request against
  the repository that declares it. The owner merges; never write to main. When
  the cause was a hand edit, the pull request also adds the guard that would
  have put it back: an expiry, a restore step, a drift check.
- **Finance:** post to #finops: the line, the cause, the owner, dollars per day
  and per month, and the pull request. No diffs.
