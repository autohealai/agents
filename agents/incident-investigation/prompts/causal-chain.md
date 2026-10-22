# The causal chain

A root cause is not a sentence, it is a chain. Write the chain out, one link per
line, from the change that started it to the impact the customer felt.

```
<change> → <first-order effect> → <second-order effect> → … → <customer impact>
```

Rules:

- **At most five links.** More than five and you are narrating a trace rather
  than explaining a mechanism; fold the middle.
- **Every link cites its evidence**, as `#ev-<n>` — the id of the tool result
  that shows it. A link you cannot cite is an inference, and it is marked
  `(inferred)` rather than dropped.
- **Each link states a mechanism, not a correlation.** "retry budget raised
  from 2 to 5" → "each failed call now occupies a pool slot 5× longer" is a
  mechanism. "retries went up and latency went up" is not.
- **The last link is what a customer experienced.** If the chain ends at a
  metric, it is not finished.

## Example

```
1. payment v2.14.0 raised RETRY_MAX_ATTEMPTS 2 → 5 and cut the backoff
   250ms → 50ms  (#ev-7)
2. each currency timeout now holds a payment worker for ~6s instead of ~0.8s
   (#ev-11)
3. checkout's gRPC connection pool to payment (max 64) saturates  (#ev-4)
4. checkout requests queue behind the pool and hit the 30s client deadline
   (#ev-9)
5. customers see the checkout button spin and then fail  (#ev-2)
```
