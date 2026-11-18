# Confluence

What the Confluence skill must tell agents about this customer's Confluence: which spaces hold runbooks, architecture docs and postmortems, and the ids of the pages agents should open first. The tools have no search, so agents reach a page only by its id or by walking down the page tree; record the ids.

## Capture

- **Deployment:** Cloud (`https://acme.atlassian.net/wiki`) or Data Center (`https://confluence.acme.com`). It decides what a space id is and which tools work, so state it first.
- **Spaces:** each space that matters, by key, name and what it holds (`OPS` Operations: runbooks; `ENG` Engineering: architecture and ADRs; `INC` Incidents: postmortems). On Cloud add each space's numeric id (`98306`).
- **Entry pages:** the id and title of each space's home page and of the index pages agents start from (`Runbooks` in `OPS`, id `123456789`).
- **Runbooks:** for each key service, its runbook's page id and title (Checkout: `Checkout runbook`, id `223344556`), and how runbooks are titled (`<Service> runbook`, `SOP: <process>`).
- **Postmortems:** where they live (a parent page, a space, blog posts) and how they are titled (`2026-10-14 Checkout outage`).
- **Freshness:** pages the person calls stale or superseded, and the page that replaced each.

## Ask the person

- Which spaces hold the runbooks, architecture docs and postmortems agents should read, and which can they ignore?
- Which pages do you open first when an alert fires or a customer complains?
- Which runbooks are out of date?

## Explore

- `confluence_test_connection` first: it says Cloud or Data Center and the base URL.
- Spaces: `confluence_get_spaces` with `limit: 100`. Cloud returns each space's `id`, `key`, `name` and `homepageId`; Data Center returns the `key`, with the home page under `_expandable.homepage`.
- A space's tree: from its home page id, `confluence_get_page_children` one level at a time (`limit: 50`). `confluence_get_page_descendants` returns a whole subtree: use it only on an index page.
- A page: `confluence_get_page_by_id`, on Cloud with `body-format: "storage"`. Its version date tells you how fresh it is.
- Where a page sits: `confluence_get_page_ancestors` with its id.
- A page the person names: take the id from its URL (Cloud `/wiki/spaces/OPS/pages/123456789/...`, Data Center `viewpage.action?pageId=123456789`).

## Guardrails

Write the ones agents will hit into the skill.

- There is no search and no CQL: agents find a page by its id or by walking down from a page whose id they know. Write the ids.
- `confluence_get_pages` lists pages across the whole site with no space filter: do not page through it to find something.
- A space tool's `id` is the numeric space id on Cloud and the space key on Data Center.
- On Cloud, page tools return a page's text only with `body-format` (`"storage"` or `"atlas_doc_format"`). Data Center always returns the storage body.
- Data Center has no site-wide listing of labels, comments, attachments, users, tasks, folders, whiteboards, databases, smart links or custom content: those tools fail there.
- `limit` is at most 250. The next page on Cloud takes the `cursor` from the response's `_links.next`; on Data Center `cursor` is a numeric offset.

## Pitfalls

- The `spaces` table has no key column: write `name` as the space name with its key (`Operations (OPS)`). The `description` is the person's.
- `important_pages` holds full page URLs, not titles or ids. Add a URL only when the person named the page or you confirmed it is a runbook they use; put each page's id in the skill.
- A Data Center URL like `/display/OPS/Checkout+runbook` carries no id: find the page in the space tree before you write its id.
- Personal spaces (`~username`) and archived spaces crowd the list: leave them out unless the person names one.
- No tool filters pages by label: do not write label-based lookups into the skill.

## Leave out

CQL, storage-format markup, REST API versions, page contents, and page lists agents can walk themselves.
