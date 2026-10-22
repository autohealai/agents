---
name: Triaging a support escalation from the customer's own evidence
description: >-
  Find what failed for this customer, from their session, their account's
  logs and their Sentry events, before matching the ticket to a known issue;
  then link the known issue or hand a new bug to its owner in a form they can
  reproduce. Use on every ticket support escalates to engineering.
---

# Triaging a support escalation from the customer's own evidence

> Written after PYL-4736 was matched to the old 3-D Secure timeout because it
> quoted "Payment declined". The customer had never seen a 3-D Secure prompt.
> Their saved card was failing a vault lookup, a different issue with the same
> message, and the workaround we sent did not help.

The message a customer quotes is the least specific thing in the ticket.
payment shows "Payment declined. Please try another card." for every
rejection it receives. Start from what happened to this customer, and match
last.

## 1. Replay the customer's session first

Find the session in FullStory by the requester's user id, around the time the
ticket gives. Note what they did, what they saw, which request failed, its
status and how long it took, and what they tried after. A failure in 400ms
never reached a bank; one that runs to 30 seconds is a timeout. Note what did
NOT happen, too: no 3-D Secure frame, no redirect, no retry prompt.

## 2. Filter by the customer's account and release

Search logs with `@account_id:<id>` across the services on the failing
request, over the session window. Pull Sentry events with `account_id:<id>`
and the release the session hit. Write down four things: the exception, the
top in-app stack frame, the release, and any attribute that sorts the events
(currency, card network, region, saved card or new).

## 3. Match on the stack trace and the release

| A candidate known issue has | Verdict |
|---|---|
| the same exception and top frame, and the customer's release is in its range | known issue: link it |
| the same message, but a different frame or release | not a match: say which differed |
| nothing with this frame | new bug: file it |

The number of earlier tickets that quoted the same message is not evidence.

## 4. Known issue: link it, do not duplicate it

Link the ticket to the existing Jira. Quote its status and, if it has one,
the release the fix ships in. Add nothing to engineering's queue.

## 5. New bug: file it so the owner can reproduce it

The owner is the team that owns the service in the top frame, from the
catalog, not the team that owns the page the customer was on. File a Bug in
Jira project SHOP with:

- the FullStory session link and the time of the failing request
- reproduction steps a teammate can follow in staging, with expected and actual
- the Sentry issue, one event id, and the release
- the suspected commit, if Sentry or the release diff names one
- every ticket with the same exception, so each customer hears about the fix

Engineering accepts the bug into a sprint. Do not set a sprint or a fix
version. Post the hand-off in #support-escalations.

## 6. The reply draft

Support sends the reply; draft it for them. Say plainly whether the fault is
ours. Give a workaround the customer can use today, and only one this
customer's evidence shows will work. Give the Jira reference, not a date
nobody has agreed.

## 7. When the fix ships

When the pull request linked to the Jira reaches production, update every
linked ticket, tell the account's CSM in #support-escalations, and draft the
follow-up for support to send.
