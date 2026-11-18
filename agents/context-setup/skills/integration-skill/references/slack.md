# Slack

What the Slack skill must tell agents about this customer's workspace: which channels carry alerts and incident discussion, their channel ids, and which apps post what. The tools take channel ids and have no message search, so record the ids.

## Capture

- **Channels:** each channel that matters, by name and id, with what it carries (`#checkout-alerts` `C04ABCD1234`: Datadog monitors for Checkout; `#incidents` `C01EFGH5678`: incident threads). Mark the private ones.
- **Alert sources:** which app posts in which channel (Datadog, PagerDuty, Sentry, a CI bot), how its message names the service and severity (`[P1] checkout-api: error rate > 5%`), and whether the detail is in the message text or in an attached card.
- **Incident flow:** where an incident is declared and discussed (a thread on the alert, a new `#inc-<date>-<name>` channel), and the reactions or replies that mean acknowledged or resolved (`:eyes:`, `:white_check_mark:`).
- **On-call groups:** the user group handles that reach a team, with their ids (`@checkout-oncall`, `S05IJKL9012`).
- **Where agents post:** the channel and form for agents' findings, when the person wants agents to post (a reply in the alert's thread rather than a new message).
- **Noise:** channels and bots the person says to ignore.

## Ask the person

- Which channels carry alerts and incident discussion for the services that matter?
- Which bot alerts are noise, and which mean customer impact?
- Should agents post their findings in Slack, and where?

## Explore

- `slack_test_connection` first: it names the workspace.
- Channels: `slack_list_channels` returns each channel's `id`, `name`, `is_private`, `num_members`, `topic` and `purpose`. Pick candidates by name and purpose (`alert`, `incident`, `oncall`, a service name).
- Recent messages: `slack_get_channel_history` with the channel id, `limit: 20` and `oldest` a week ago as Unix seconds (`"1794268800"`). A `not_in_channel` error means the Autoheal app is not a member.
- An app's message: `slack_get_thread_replies` with the channel id and the message's `ts` returns the app's name, its card fields and its Block Kit text, which channel history strips.
- On-call groups: `slack_list_usergroups`.
- A user id in a message: `slack_get_user_info`.

## Guardrails

Write the ones agents will hit into the skill.

- Every tool takes a channel id (`C04ABCD1234`), never `#name`.
- There is no message search: agents read a channel's history in a time window, then the threads that matter.
- `slack_get_channel_history` returns at most 50 top-level messages, without thread replies, app names, attachments or blocks. Read alert details and replies with `slack_get_thread_replies`, passing the parent message's `ts`.
- `oldest` and `latest` are Unix seconds as strings. A message's `ts` (`1794268800.123456`) is its id: pass it exactly as returned.
- The app reads only channels it is a member of, and agents cannot join one: someone runs `/invite @Autoheal` in the channel. A private channel appears in `slack_list_channels` only after that.
- Slack throttles history and thread reads per app, down to one call a minute on its restricted tier: read the few channels that matter, and on `ratelimited` wait before you retry.

## Pitfalls

- The `channels` table has no id column: write `name` as the channel name (`#checkout-alerts`) and keep the ids in the skill. The `description` is the person's.
- A channel that returns `not_in_channel` still belongs in the table when the person wants it: say in your reply that someone must invite the app.
- Channel names change and ids do not: when the person gives a name, look up its id with `slack_list_channels` before you write it.
- Bot cards differ by app and by alert type: describe a format only from messages you read, not from what the app usually sends.

## Leave out

Slack API mechanics, rate-limit tiers, message JSON fields, message contents, user emails, and recent message or alert counts.
