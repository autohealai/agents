# Dynatrace

What the Dynatrace skill must tell agents about this customer's tenant. Agents already know DQL and Dynatrace's problem and entity model; record what is true only here.

## Capture

- **Tenant type:** SaaS with Grail (OAuth client configured) or Managed / API token only. It decides which tools work, so state it first.
- **Data the customer uses:** of Problems, Metrics, Logs, Traces, Business events, User sessions, SLOs and Change events, the ones they rely on.
- **Scoping:** the management zone or tag that means "an environment", and its values (zone `Production`; tag `environment:prod`). Write both forms: `managementZones("Production")` for problems, `mzName("Production")` for entities.
- **Key services:** each important service's entity selector and its resolved id (Checkout: `type("SERVICE"),entityName.equals("checkout")` is `SERVICE-ABC123`). The id saves agents a lookup every incident.
- **Metrics:** the `dt.*` metric keys they watch and what each means to them (`dt.service.request.response_time` is checkout latency).
- **Logs and traces:** how a service is identified in logs and spans (`dt.entity.service`, or `k8s.namespace.name` / `k8s.workload.name`), and the log fields that matter (`loglevel`, `status`, `content`).
- **Business events:** each stream as `event.provider` / `event.type`, and what the key attributes mean, with units (`amount` = order total in USD).
- **User sessions:** the RUM application names, filtered by `useraction.application`.
- **SLOs:** the SLO names that matter and the service each one measures.
- **Deployments:** how they record them: classic `event.type == "CUSTOM_DEPLOYMENT"`, or SDLC `event.kind == "SDLC_EVENT" and event.type == "deployment"`.

## Ask the person

- Which services matter most in an incident, and which environment is production?
- Which metrics or SLOs mean customer impact for them?
- Which management zones or tags belong to which team?
- Which problems or alerting rules are known noise?

## Explore

- `dynatrace_test_connection` first: it says whether the API token works and whether Grail (OAuth) is configured.
- Services, zones and tags: `dynatrace_list_entities` with `entity_selector=type("SERVICE")` and `fields=+properties.detectedName,+tags,+managementZones`.
- Recent problems in a zone: `dynatrace_list_problems` with `managementZones("<zone>")` over the last days.
- Grail only: sample fields with `fetch logs | fields dt.entity.service, k8s.namespace.name, loglevel | limit 5`; spans per service with `fetch spans | summarize count(), by:{dt.entity.service} | limit 20`; bizevent streams with `fetch bizevents | summarize count(), by:{event.provider, event.type} | limit 50`; RUM apps with `fetch user.sessions | summarize count(), by:{useraction.application} | limit 50`; deployment events with `fetch events | summarize count(), by:{event.type, event.kind} | limit 50`; SLOs with `dynatrace_list_slos`.

## Guardrails

Write the ones agents will hit into the skill.

- Metrics, logs, spans, events, bizevents, sessions and SLOs need Grail and OAuth (SaaS only). Problems, entities and metric events work on the API token, Managed included.
- Each query tool accepts only its own table: `dynatrace_query_logs` takes `fetch logs`, `dynatrace_query_spans` takes `fetch spans`, and so on.
- `dynatrace_query_metrics` takes a metric key with an optional aggregation (`dt.host.cpu.usage:max`): only `avg`, `min`, `max`, `sum`, `count`, `median`; no percentiles such as `:p99`, no `|`, no `by:{}`. Results are environment-wide.
- `mzName(...)` is not valid in the problems selector: use `managementZones(...)`. Problem severity has no `INFO`.

## Pitfalls

- A fresh form lists every feature unselected: that is "none selected", not "no features". Probe each data type and note in each row's `agent_findings` whether it is reachable.
- On a Managed or token-only tenant, do not write Grail sections: the queries would fail every time.
- The scoping, service and deployment dropdowns take patterns with placeholders (`mzName("<ENV>")`, `filter dt.entity.service == "<SERVICE_ID>"`) as options; the person picks the value.
- The RUM application is `useraction.application`, not `application`.

## Leave out

DQL syntax, the selector grammar, what generic fields such as `request.is_failed` mean, and examples that do not use this customer's zones, services or metric keys.
