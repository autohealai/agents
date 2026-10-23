---
name: Diagnosing a retry storm
description: >-
  Recognise the signature of a client-side retry storm — a downstream latency
  bump amplified by a retry policy until an upstream pool saturates — and
  separate it from a genuine downstream outage. Use when an upstream service is
  slow or erroring but its dependency looks healthy.
---

# Diagnosing a retry storm

> Synthesised from four investigations between 2026-08-19 and 2026-09-08, in
> which the same mechanism was re-derived from scratch each time.

A retry storm is the case where **the dependency is fine and the caller is
drowning in its own retries**. It reads at first like a downstream outage,
which is why it costs an hour to find if you do not know the shape.

## The signature

All four of these together, and it is a retry storm:

1. The upstream service is slow or erroring; its **dependency's own** p99 and
   error rate are flat.
2. The dependency's *request* rate is up by roughly the retry multiplier —
   3×–5×, not 1.2× — with no corresponding rise in unique upstream requests.
3. The upstream's connection-pool or worker saturation is at or near 100%,
   and its queue depth is growing.
4. Request rate at the edge is inside the normal band. Load did not
   increase; each request started holding resources for longer.

If the dependency's own error rate is up, stop — that is a downstream problem
and the retries are a symptom.

## Where the change usually is

Look for a change to the **retry policy**, not to the logic: `max_attempts`,
the backoff base, the jitter, a per-call timeout, or a circuit breaker
threshold. These land in config files and Helm values, so they are easy to
miss when you are reading application diffs.

Two multipliers stack and this is the thing people miss: raising attempts from
2 to 5 while cutting the backoff from 250ms to 50ms does not raise the load
2.5×, it raises the time a call occupies a pool slot by far more, because the
failed attempts now arrive before the earlier ones have released.

## The arithmetic that settles it

```
slot-seconds per request ≈ attempts × (per-attempt timeout + backoff)
pool headroom            ≈ pool size / (slot-seconds × request rate)
```

Run it for the old policy and the new one. If the new number crosses 1.0 at
the observed request rate, you have the mechanism, not a correlation — and you
have it without waiting for another occurrence.

## What NOT to conclude

- Not "the dependency is degraded" — check its own series first.
- Not "we need a bigger pool" — a bigger pool moves the saturation point, it
  does not remove the amplification.
- Not "traffic spiked" — check the edge rate against the previous seven days
  before saying so.
