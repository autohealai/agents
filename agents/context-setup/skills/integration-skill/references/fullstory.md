# Fullstory

What the Fullstory skill must tell agents about this customer's Fullstory org. Agents already know what session replay is and what the Fullstory tools return; record what is true only here.

## Capture

- **Key tier and plan:** the API key's tier (`USER`, `ARCHITECT` or `ADMIN`) and whether session summaries and events return data. It decides which tools work, so state it first.
- **Identity mapping:** what `uid` is (the internal account id, a user id) and whether the email domain identifies the customer org. This matters most: it turns a Fullstory user into an affected customer.
- **Coverage:** the domains and apps the Fullstory snippet runs on (`app.acme.com`, the iOS app), and the environments it runs in (production only, or staging too).
- **Anonymous flows:** the flows where users are not identified yet (sign-up, guest checkout), so agents know those sessions cannot be found by user.
- **Segments:** the names of the saved segments that mean errors or customer impact ("Checkout errors", "Rage clicks on payment").
- **Lookup that ran:** the identifier that found sessions for a known user (`email`, or `uid` = account id).

## Ask the person

- How does a Fullstory `uid` or email map to one of your customer accounts?
- Which domains, apps and environments run the Fullstory snippet?
- Can you give one user's email or `uid` to check the lookup with?

## Explore

- `fullstory_test_connection` first: it returns the org and the key's tier.
- Segments: `fullstory_list_segments` with `limit=50`.
- Identity: `fullstory_list_user_sessions` with the `email` or `uid` the person gave.
- Plan check: on one returned session, `fullstory_get_session_summary`, then `fullstory_get_session_events` with `errors_only=true`. A 403 here settles which tools agents can use. When they work, the page URLs in the events show the domains the snippet runs on.

## Guardrails

Write the ones agents will hit into the skill.

- `fullstory_get_session_summary` and `fullstory_get_session_events` need an `ARCHITECT` or `ADMIN` key and the "Anywhere: Activation" plan feature; otherwise they return 403. `fullstory_test_connection` and `fullstory_list_user_sessions` work without either. When they 403, write that agents use only `fullstory_list_user_sessions` and `fullstory_list_segments`.
- `fullstory_list_user_sessions` needs a `uid` or an `email`. No tool finds sessions by URL, time or error.
- Pass `session_id` exactly as `fullstory_list_user_sessions` returns it (`<user_id>:<session_id>`).
- `fullstory_list_segments` returns the saved segments, not the sessions in them. Those need a Data Export job, which no tool runs.
- Start with the summary, then call `fullstory_get_session_events` with `errors_only=true`; a full event stream is large.

## Pitfalls

- No sessions for a known user does not mean no impact. The app may not call `FS('setIdentity')` on that flow, or the `uid` is not the value you tried.
- No tool lists environments or instrumented properties. Infer them from page URLs in session events and ask the person to confirm.
- The three form fields are free text. Write `customer_id_mapping` in plain words (`uid` = internal account id; email domain = customer org) and mark what the person has not confirmed.

## Leave out

What Fullstory is, the list of Fullstory tools and their outputs, the snippet API beyond `setIdentity`, and examples that do not use this customer's domains, segments or identity mapping.
