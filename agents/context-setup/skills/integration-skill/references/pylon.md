# Pylon

What the Pylon skill must tell agents about this customer's support desk. Agents use Pylon tickets to read what customers report, find similar past tickets and learn how they were resolved; a new ticket can also start a run. Record what is true only here.

## Capture

- **Ticket vocabulary:** the words customers and support use in titles for recurring problems (`checkout failing`, `webhook not delivered`, `SSO login loop`), so agents search with terms that match.
- **Mapping to services:** how a ticket points at a product area or service here: a tag, a custom field, the account, or title words (tag `billing` = Billing service; custom field `Product area` = `Checkout`).
- **States in use:** which of `new`, `waiting_on_you`, `waiting_on_customer`, `on_hold` and `closed` the team uses, and what a resolved ticket looks like (closed, with the cause in an internal note).
- **Where the cause is written:** internal notes, a linked issue (Jira, Linear, GitHub) or a custom field, so agents read the right part of a ticket.
- **Priority accounts:** the accounts the person names as priority (enterprise or regulated tiers), as they appear in `account`.
- **Environments:** the environments tickets come from and how a ticket shows which one (a tag, a custom field, the account).
- **Not engineering:** the ticket types agents should skip (billing questions, feature requests), and how to recognise them.
- **Searches that work:** each `pylon_search_issues` call written into the skill, with the window it ran on and what it found.

## Ask the person

- Which product areas or services generate the most tickets, and what words do customers use for them?
- Where do engineers write down the root cause of a ticket: internal notes, a linked issue, or a field?
- Which accounts get priority treatment?
- Which ticket types are not engineering problems and should be skipped?

## Explore

- Recent tickets: `pylon_search_issues` with `start_time` 30 days ago, `end_time` now and `limit=25`; read titles, states and accounts.
- Resolved tickets: the same with `state=closed`, then with `title_contains` set to a few recurring terms from the titles you saw.
- Ticket detail: `pylon_get_issue` on three or four tickets, for tags and custom fields.
- Resolution trail: `pylon_get_issue_messages` with `limit=20` on two closed tickets, to see whether the cause lives in internal notes or a linked issue.
- `pylon_test_connection` only when these calls fail.

## Guardrails

Write the ones agents will hit into the skill.

- `pylon_search_issues` filters only by `state`, `title_contains`, `body_contains` and a creation window (`start_time` / `end_time` in ISO 8601, `2026-11-01T00:00:00Z`). It has no tag, account, assignee or priority filter: search the words that go with them, then filter the results.
- `title_contains` and `body_contains` match a substring, not words or synonyms. Search the short phrase customers use, and try a second phrasing before concluding there are no matches.
- `state` takes one value per call.
- Search returns at most 100 tickets and has no cursor. Narrow the time window instead of paging.
- `pylon_get_issue_messages` returns 20 messages by default; pass `pagination.cursor` back as `cursor` for long threads.
- A 429 carries a retry hint. Make calls one at a time.

## Pitfalls

- The opening message is the customer's description, not a diagnosis. Read the internal notes and later replies for the cause.
- The form has one field, `environments` (comma-separated). Fill it only with environments that tickets or the person showed. Everything else goes in the skill.
- Record vocabulary and conventions, not ticket counts or open-ticket lists: those go stale within a day.

## Leave out

What Pylon's states mean in general, live queues and counts, individual tickets, and customer data: never copy requester names, emails or ticket bodies into the skill, and name accounts only when the person lists them as priority accounts.
