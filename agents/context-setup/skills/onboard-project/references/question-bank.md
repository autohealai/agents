# Question bank

One section for each interview category, in the order to ask them. Each section has:

- **Explore first**: what to read with tools before you ask. Show the result, and ask the person to confirm or correct it.
- **Ask**: the question that matters. Ask it as one question, with options when you have them.
- **Follow-ups**: ask these only when the first answer leaves them open.
- **Writes to**: where the answer goes. The templates are in `skill-shapes.md`.

Each category also gets the five moves from Step 3 of the skill: pick the integration, explore, narrow to the domain, get the pattern, write it. A category with no connected integration still gets its question: write the answer with `> UNTESTED: <tool> is not connected`, and record the connect link as a gap.

## 1. Domain and components

**Explore first.** The docs from Step 2. The service entities in the Context Graph that the team owns. When a ticketing integration is connected: the domain's incidents of the last 90 days, counted by configuration item, component or service field.

**Ask.** "What does this domain do for the business, and what are its main components?" Offer the component list that you found, ranked by incident count, and ask which three to five to cover first.

**Follow-ups.**
- What does each component do, in one line? Which one starts the main flow, and which one ends it?
- Where does data come from, and where does it go (upstream and downstream systems, and the teams that own them)? Which steps are real-time, and which are batch (and on which schedule)?
- Which paths are critical: if a step stops, what does the business lose, and how soon?
- Which data stores does the domain use?
- Environments and regions. Hours of operation (24x7, business hours, a batch window).
- What is outside the team's control (a shared platform, a vendor, another team's service)? Incidents that cross domains usually start there.
- Subdomains, if any, and whether a subdomain has its own on-call team.

**Writes to.** `<domain>-architecture`. Services in the Context Graph (Step 6).

## 2. Alert sources

**Explore first.** The alert-source integrations (PagerDuty, Opsgenie, Alertmanager, Datadog monitors, ServiceNow, a scheduler that sends alerts). Read the last 20 alerts or incidents for the domain and look at the fields of their payloads.

**Ask.** "What in an alert tells you that it belongs to this domain?" A tag, an assignment group, a routing key, a service field, or a prefix in the alert name. Show the payload fields that you found.

**Follow-ups.**
- Which field names the component? Which field names the environment and the region?
- Severity scale: which values are a major incident?
- Which alerts are noisy and usually closed with no action?
- Has a real alert reached Autoheal yet? Until one has, automatic triage is not verified: say so in the report.

**Writes to.** The alert source's integration skill, `## Team:` section.

## 3. Logs and traces

**Explore first.** The log integration's label, index, field or tag values. For example, the label values of a Loki data source, the Dynatrace management zones and entity tags, the Datadog `service` values, or the Elasticsearch indexes. Match them to the component names.

**Ask.** "Which label or field selects this domain's logs, and which selects one component?" Offer the pattern that you found, such as `{component="<COMPONENT>", env="<ENV>", region="<REGION>"}`.

**Follow-ups.**
- Which components do not send logs to this tool? Where are their logs (files on a host, another tool)?
- Paste one or two queries that you run during an incident. Store them verbatim, then run them.
- Do traces use the same filter? Which field links a log line to a trace or a request (a correlation id)?
- Which fields carry business ids (an order id, a batch id, a trade id)? Investigations search on them.
- Log retention: how far back can an investigation look?

Run one query for the domain and one for a component, over the last hour, with a limit. Write the query and the result count.

**Writes to.** The log integration's skill, `## Team:` section. The component skills, "Logs".

## 4. Metrics

**Explore first.** Metric names and label values for the domain's components, for example `label_values(<label>)` on a Prometheus data source, or the metric selector in Dynatrace.

**Ask.** "Which label selects this domain's metrics, and which signals tell you that a component is unhealthy?"

**Follow-ups.**
- Golden signals for each component: requests, errors, latency, saturation, queue depth, batch lag.
- SLOs or error budgets, if any.
- The dashboards that they open first, with links.

Run one query for each signal that you write.

**Writes to.** The metrics integration's skill, `## Team:` section. The component skills, "Metrics" and "Dashboards".

## 5. Cloud runtime

**Explore first.** With `bash` and the cloud CLI: the accounts or subscriptions that you can see (`aws sts get-caller-identity`, `az account list`), Kubernetes namespaces (`kubectl get ns`), and resource tags. Limit each command.

**Ask.** "How do you find this domain's resources: a tag (`team=<TEAM>`), a name prefix, a namespace, or a dedicated account or subscription?" Offer the patterns that you found.

**Follow-ups.**
- Which accounts or subscriptions, which clusters, and which regions?
- Hosts that are not in the cloud (on-premises servers, VMs). Where is their inventory (a CMDB, tags, a spreadsheet)? When there is no single inventory, record each source.
- How does an engineer get a shell or logs on a host?

**Writes to.** The cloud integration's skill, `## Team:` section. `<domain>-architecture`, "Environments and regions".

## 6. Code

See `code-exploration.md`. Ask this category after the categories above, so that you know the component names.

**Writes to.** `<domain>-codebase`, the component skills ("Code"), and `team` labels on repositories.

## 7. Deploys

"What changed?" is the first question in most investigations, and a deploy is the most common answer. Ask these five questions in this order:

1. **Which integration holds the deploy record, and which resource in it?** A GitHub Actions workflow, a GitLab pipeline, an Azure DevOps release, an Argo CD application, a change request in ServiceNow. Name the resource, not only the tool.
2. **Which field on that resource names the component?** Ask for the field, not one value.
3. **The release naming scheme.** Read the last few releases with the integration and read the pattern back to the person: `v1.24.3`, `payments-2026.08.14` and a bare commit SHA mean different things when an agent looks for "the deploy before the alert".
4. **How do hotfixes differ from planned releases** (another pipeline, branch or approval)? The deploy that causes an incident is often the out-of-band one.
5. **How often does the team ship?** Ten times a day or once a month changes how much "a deploy happened recently" means.

Also ask about changes that are not deploys: configuration changes, feature flags, database changes, scheduler changes.

**Writes to.** The deploy integration's skill, `## Team:` section. `<domain>-codebase`, "Find the change before an incident".

## 8. Data stores

**Explore first.** The database integrations. The connection strings and schema names in the code (Step 4).

**Ask.** "Which databases and schemas does the domain use, and which table must an investigation never query?"

**Follow-ups.**
- The key tables and columns: status columns, timestamps, the ids that link to logs and tickets.
- The read queries that they run during incidents, pasted. Store them verbatim.
- Access limits: read-only, a query timeout, approved queries only, hours when queries are not allowed.

Run a query only if it is read-only, limited (`TOP 10` / `LIMIT 10`), and does not touch a table on the never-query list. When the person says that only approved queries may run, run only the queries that they pasted.

**Writes to.** `<domain>-data`.

## 9. Ticketing

**Explore first.** The ticketing integration (ServiceNow, Jira, Azure DevOps boards): the assignment groups, projects or areas that appear on the domain's recent incidents.

**Ask.** "Which assignment groups, projects or queues hold this domain's incidents, and which field names the component?"

**Follow-ups.**
- The fields that agents must read: severity or priority scale, configuration item, category, resolution notes.
- Which labels or states mark a major incident or a postmortem?
- Do incidents from other domains often come to this team (or go from it)? Which groups?

**Writes to.** The ticketing integration's skill, `## Team:` section.

## 10. Comms

**Explore first.** The chat integration's channels with the domain's name.

**Ask.** "Which channel gets this domain's alert notifications, and is the incident channel a different one?"

**Follow-ups.**
- Owners and subject-matter experts for each component (names, not only a group).
- The escalation path, and the on-call schedule if there is one.

**Writes to.** The team's `notification_channels` in the Context Graph (Slack channels only). The component skills, "Owners". Other channels go in `<domain>-architecture`.

## 11. Incident history

**Explore first.** The domain's incidents of the last 90 days. Group them by component and by similar descriptions, and read the resolution notes of the largest groups.

**Ask.** "These incidents repeat: <groups with counts>. Which are worth a check list, and how do you diagnose and fix them?"

**Follow-ups.**
- For each pattern: the first checks, the cause, the fix, and who can do the fix.
- Any recurring incident that is not in the tickets (one that is handled in chat, or a manual daily check).

**Writes to.** `<domain>-incident-patterns`. Failure modes in the component skills.
