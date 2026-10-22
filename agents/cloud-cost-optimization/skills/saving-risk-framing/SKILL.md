---
name: Stating a saving and its risk together
description: >-
  Put a number on what a cost change saves and a named risk beside it, and rank
  by saving-per-unit-risk rather than by saving. Use before proposing any change
  to a cloud bill line.
---

# Stating a saving and its risk together

A saving with no risk stated is not an opportunity, it is a trap. Every cost
change buys money with something, and the something is usually headroom, and
headroom is invisible until the day it is not there.

## The three parts, always together

```
change    what would actually be done, specifically enough to estimate
saving    $/month, from the line it comes out of, for a stated period
risk      low | medium | high, with the SENTENCE that justifies it
```

The risk word on its own is decoration. What makes it useful is the sentence:
what would have to happen for this change to hurt, and how would you know.

## What each risk level means here

**Low** — the resource is doing nothing that anything depends on, or the change
is reversible in minutes with no data loss. Routing changes, storage class
moves, deleting an unattached volume older than the backup window.

**Medium** — it reduces headroom or changes a behaviour under load, and it can
be reverted but not instantly. Right-sizing something with a known steady
profile. Reserved-capacity commitments.

**High** — it reduces headroom on a path that has already been saturated, it
loses data, or reverting it requires a rebuild. Right-sizing a pool that
absorbs a peak. Shortening a retention window.

## Rank by saving-per-unit-risk, not by saving

The largest number on the page is very often the one that should not be taken,
because the largest single expense in a well-run system is usually the capacity
that keeps it up.

Ranking by raw saving puts that change at the top of the list, and a list read
top-down is a list acted on top-down.

## Say plainly when a line should stay where it is

A cost report with no declined items has not looked hard enough. If the second
largest saving is headroom that has already proved it was needed, write that
down as a **declined** opportunity with the incident that proves it, rather than
leaving it off the list.

Leaving it off means the next report finds it again, and someone may act on
it without the context.
