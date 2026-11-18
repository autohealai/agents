# Notion

What the Notion skill must tell agents about this customer's workspace. Agents already know Notion's page, block and database model; record where this customer keeps the docs agents need, and the ids that reach them.

## Capture

- **Reach:** the integration sees only the pages and databases shared with it. Record what it can see, and name anything the person expects that it cannot.
- **Where docs live:** the databases and top-level pages that hold runbooks, architecture docs, postmortems and service docs, each with its id and URL (Runbooks database `1a2b...`; Engineering wiki page `3c4d...`).
- **Database schemas:** for each important database, the property names and types agents filter on, spelled exactly, with their options (`Service` select: `Checkout`, `Payments`; `Status`: `Published`, `Draft`; `Last reviewed` date).
- **Queries that work:** the `notion_query_database` filter that finds a service's runbook (`{"property": "Service", "select": {"equals": "Checkout"}}`), and the id it ran against.
- **Mapping to services:** how a page is tied to a service here: a select or relation property, a title convention (`Runbook: Checkout`), or one parent page per service.
- **Search terms:** the words this team puts in titles (`Runbook:`, `RCA -`, `On-call`), since search matches titles only.
- **Important pages:** the pages the team opens first in an incident (on-call handbook, escalation page), with ids.
- **Freshness:** which databases are kept current and which are stale (last edited over a year ago), so agents weigh old pages accordingly.

## Ask the person

- Which databases or pages hold the runbooks and architecture docs the team trusts?
- Which pages do they open first when debugging a failure, an alert or a customer complaint?
- Which spaces are out of date or should be ignored?
- Is any important page not yet shared with the integration?

## Explore

- `notion_test_connection` first.
- Databases: `notion_search` with `filter=database` and `page_size=20`, then with `query` set to likely title words (`runbook`, `postmortem`, `architecture`, `on-call`).
- Pages: `notion_search` with `filter=page` and the same words.
- Schema: `notion_retrieve_database` on each important database.
- Rows: `notion_query_database` with `page_size=5` on each important database, to see real property values and `last_edited_time`.
- Content: `notion_retrieve_block_children` with `page_size=20` on one or two pages, to see how they are structured.
- Pages from the form: take the id from each URL in `important_pages` (the trailing 32 hex characters) and read it with `notion_retrieve_page`.

## Guardrails

Write the ones agents will hit into the skill.

- `notion_search` matches titles only, not body text, and returns at most 20 results per call; page with `start_cursor`. Search the words people put in titles.
- An empty search result can mean the page is not shared with the integration, not that it does not exist.
- `notion_retrieve_page` returns a page's properties, not its body. Read the body with `notion_retrieve_block_children` (at most 100 blocks per call; page with `start_cursor`). Toggles, columns and other nested blocks need a call on the child block's id.
- `notion_query_database` filters name properties exactly as the database spells them, case and spaces included.
- Notion allows an average of three requests per second. A 429 says how long to wait; make calls one at a time.

## Pitfalls

- The tools call Notion API version `2025-09-03`, where a database holds one or more data sources. `notion_search` with `filter=database` returns `data_source` objects, whose `id` is not the database id (`parent.database_id` is). Run `notion_retrieve_database` and `notion_query_database` on one database during setup, and record in the skill which id each accepted and where the property schema came from.
- A database row is a page: its fields are in `properties`, its body comes from `notion_retrieve_block_children` on the row's id.
- Relation properties hold page ids only. Record the related database and what its ids stand for, so agents do not resolve them one by one.
- In `spaces`, add each database or top-level page you found as a row under its Notion name; `description` and `selected` are the person's. Put its id and what it holds in the skill.
- `important_pages` takes full page URLs (`https://www.notion.so/...`). Add one only when the person names it.

## Leave out

Notion's block types, the filter JSON grammar, the page and database model, and pages agents can find by searching their title.
