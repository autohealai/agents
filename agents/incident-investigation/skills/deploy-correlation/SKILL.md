---
name: Correlating a symptom with a deploy
description: >-
  Line a symptom's onset up against the deployments and config changes that
  preceded it, and decide which one is a candidate cause rather than a
  coincidence. Use at the start of any latency, error-rate or saturation
  investigation.
---

# Correlating a symptom with a deploy

Most of our incidents follow a change. This is how to find which one without
blaming the nearest deploy by reflex.

## 1. Fix the onset to the minute

Take the first metric that moved, not the first alert that fired — alerts carry
an evaluation window, so they lag the symptom by the window's length. Read the
raw series and note the first bucket outside the normal band.

## 2. List every change in the preceding two hours

Include all of these, because only the first is obvious:

- deployments (`kubectl rollout history`, the GitHub deployment events)
- configuration and feature-flag changes
- changes to a **downstream** service, not just the one that is symptomatic
- infrastructure changes: node pool scaling, network policy, quota

## 3. Rank the candidates

A change is a candidate when all three hold:

- it landed **before** the onset, with a gap that the mechanism can explain
- it touches the service that is symptomatic, or something it calls
- it can plausibly produce *this* symptom — a config change to a retry policy
  can saturate a connection pool; a copy change cannot

A deploy that landed forty minutes before the onset with nothing to explain the
delay is not a stronger candidate than a config change two minutes before it.

## 4. Check the negative

Before you commit, look for the same change on a service that is **not**
symptomatic. If `payment` and `shipping` both took the same library bump and
only one of them broke, the bump is not the whole story.
