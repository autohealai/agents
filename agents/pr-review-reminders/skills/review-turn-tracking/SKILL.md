---
name: Tracking whose turn it is on a pull request
description: >-
  Decide, for each open pull request, whether it is waiting on a reviewer, on
  its author, or on nobody yet, and exactly who to remind and when. Use on every
  sweep and every review event, before sending a reminder.
---

# Tracking whose turn it is on a pull request

> Written after checkout#412 got its third daily reminder to all three of
> Checkout Squad. One of them had requested changes, one had approved, and the
> pull request had been waiting on its author for three days. Nobody reminded
> the author.

"Open longer than 36 hours" says a pull request is slow. It does not say who
is holding it. Read the reviews and the pushes in order, and the last event
tells you whose move it is.

## Whose turn

| State | Turn | Who to remind | When |
|---|---|---|---|
| Nobody requested, no reviews | author | the author, with one suggested reviewer | 4 hours after it opened |
| Requested, no reviews | reviewers | the requested reviewers; one member for a team request | 36 hours after it opened, then every 24 |
| A review since the author's last push | author | the author only | 24 hours after the latest review |
| The author pushed or re-requested after a review | that reviewer | the reviewer who reviewed last, alone | 24 hours after the push |
| Approved, checks green, not merged | author | the author, to merge | 24 hours after the approval |
| Draft, or a push, review or reply in the last 12 hours | nobody | nobody | not while it is moving |

A review with changes requested is still a review. The pull request cannot
merge, but it is not waiting on reviewers, and reminding them is noise.

## Team requests

A CODEOWNERS team request lands on every member who is not the author. Check
memory for how that team reviews before you remind anyone. Unless memory says
otherwise, remind the one member with the fewest open review requests, not all
of them. Once any member has reviewed, the team's request is answered.

## Suggesting a reviewer

When nobody was requested:

1. Read CODEOWNERS for the paths the pull request changes. Say why GitHub
   requested nobody: no rule matches those paths, the rule names a team
   that no longer exists, or the team lacks write access to the repository
   (GitHub skips it silently).
2. Take the owning team from the catalog.
3. Suggest the member of that team, other than the author, who has reviewed
   the most pull requests touching those paths in the last 90 days. One name,
   and the reason.

The suggestion goes to the author in the thread. The author requests the
review; the agent never does.

## Working hours

Read each recipient's time zone from their Slack profile. Send between 09:00
and 18:00 local. Outside those hours, schedule the message for 09:30 local.
Do not hold it for the next sweep instead; that can be six hours late.

## What the thread says

- The head carries one line for the turn: `Turn: @dkowalski (author), since
  the review with changes requested 3d ago`.
- A reminder names the one thing that is waiting: "re-review after the push 26h
  ago", "address arivera's requested changes", "approved and green, ready to
  merge".
- When someone replies that a reminder was wrong, correct the turn, say so
  once in the thread, and do not send that reminder again.
