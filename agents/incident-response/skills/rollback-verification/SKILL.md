---
name: Verifying that a rollback actually worked
description: >-
  Confirm a rollback or mitigation really cleared the incident rather than
  coinciding with a quiet minute. Use after any mitigation is applied, before
  declaring recovery.
---

# Verifying that a rollback actually worked

A mitigation is not verified because the alert cleared. Alerts clear for
reasons that have nothing to do with the fix.

## Check the mechanism, not just the symptom

Recovery is confirmed when the metric **in the middle of the causal chain**
returns to normal, not only the one at the end. If the chain was

```
retry budget → pool saturation → queueing → customer timeouts
```

then customer timeouts falling is the weakest evidence available: load drops,
traffic shifts, a cache warms. Watch pool saturation.

## Three things to confirm, in this order

1. **The changed thing is back.** `kubectl rollout history` shows the revision
   you expected, and the running pods are on it. A rollout that is still
   progressing has not rolled back yet.
2. **The middle-of-chain metric recovered**, and did so *after* the mitigation
   landed, not before. Note both timestamps. If the metric turned before the
   rollback completed, the rollback is not why.
3. **The symptom recovered and stayed recovered** for at least two full
   evaluation windows of the alert that fired.

## Watch for the load confound

If request rate fell at the same time the mitigation landed, you have learned
nothing yet — the system may simply be under less pressure. Compare against
the same rate earlier in the incident, or wait for the rate to come back.

## Write down what would make you re-open

Name the metric and the threshold that would mean it is back. "Pool saturation
above 80% for five minutes" is a re-open condition; "if it looks bad again" is
not.
