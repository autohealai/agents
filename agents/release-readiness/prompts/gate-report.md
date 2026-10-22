# Writing down a release risk

A risk is three things. Any one of them missing and the reader cannot act on
it, which makes reporting it worse than useless — it looks like diligence.

## 1. The outcome, not the diff

State what a person or a system experiences, not what the change did to the
code.

```
bad   a NOT NULL constraint is added to cart.promo_code
good  carts created by the 2026.08 clients fail to write from the moment the
      migration lands, because those clients do not send promo_code
```

The bad version is true and tells the reader nothing about whether to ship.

## 2. The team that owns it

Resolve the owner from the SERVICE through the catalog, never from the pull
request's author. Authors move between teams and often send a change into code
they do not carry the pager for.

If the service has no owning team in the catalog, that is itself the finding.
Say so rather than naming the nearest plausible squad.

## 3. The evidence

A PR number, a CI run id, or a dashboard panel — cited as `#ev-<n>` so a reader
can open the thing you read. "The canary looked fine" is not evidence; the
canary run, its window and its traffic share are.

## Severity is about the release, not the bug

Rate the outcome if this release ships as it is, inside the rollback window.
A sev1 bug behind a flag that is off is a sev4 release risk. Say which you are
rating.
