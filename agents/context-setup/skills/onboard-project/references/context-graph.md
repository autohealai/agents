# Context Graph writes

Onboarding writes four things to the Context Graph, as the person, with `context_graph_write` and the project's `project_id`. The writes save at once, with no preview, so confirm the list with the person first, then write, then say what landed from the tool's result (`created`, `updated`, `unchanged` or `failed`, for each item).

Pass `title` when you create an entity: without it, the entity is titled with its name ("payments", not "Payments"). Pass `source: {"integration_type": "onboarding", "metadata": {"skill": "onboard-project"}}` on every entity you write, so that people can see that onboarding supplied the values, next to what an import supplied.

## 1. The team

The domain's team, found or agreed in Step 0. Read it first with `context_graph_get_entity` when it exists.

```json
{"entities": [
  {"blueprint": "team", "name": "<domain>", "title": "<Team title>",
   "properties": {"description": "<one line on what the domain does>", "timezone": "<IANA zone>"},
   "source": {"integration_type": "onboarding", "metadata": {"skill": "onboard-project"}}}
]}
```

## 2. The services

One `service` entity (the `service` blueprint itself) for each component, with the team as `owner`. Only that blueprint has `owner` to a `team`, `depends_on` and the `tier-1` to `tier-4` scale.

Look in two separate calls, because the filters of one call must all match, and on a first run no service has the team as owner yet:

- The component: `context_graph_list_entities` with `blueprint: service` and `search: <component>`. This also returns imported entities, such as `pagerduty_service` or `datadog_service`; each item's `blueprint` says which.
- An earlier onboarding's services: `context_graph_list_entities` with `related_to: {relation: owner, blueprint: team, name: <domain>}`.

A match with blueprint `service` is the component: reuse its name byte for byte (rule 5). An imported entity keeps its integration's schema: its `owner` points at that integration's own team, it has no `depends_on`, and its tier scale is different. Never write `owner`, `depends_on` or `tier` to it. Create the `service` entity for the component (use the imported entity's name when it is the component's name), and link the imported entity to it with labels only: `{"blueprint": "<imported blueprint>", "name": "<imported name>", "labels": {"team": ["<domain>"], "service": ["<name>"]}}`.

```json
{"entities": [
  {"blueprint": "service", "name": "<component>", "title": "<Component title>",
   "properties": {"description": "<one line>", "tier": "tier-1", "language": "<language>",
                  "repository_url": "<url>", "documentation_url": "<link>"},
   "relations": {"owner": "<domain>", "depends_on": ["<upstream component>"]},
   "source": {"integration_type": "onboarding", "metadata": {"skill": "onboard-project"}}}
]}
```

- `owner` is what links a service to the domain. Every service that the domain owns gets it.
- `depends_on` follows the data flow from the architecture skill: a component depends on what it calls or reads from. Name only `service` entities that you found or are creating in the same call. A relation key that you send gets exactly the targets that you send, so read the entity first and send all of its targets.
- A system outside the domain (an upstream platform, another team's service) gets an entity only if you find it, or if the person asks for one. Do not set its `owner` to this team. Otherwise, describe it in the architecture skill only.
- `tier` is one of `tier-1` to `tier-4`. Ask; do not guess it.

## 3. Repository labels

Read the repositories (`context_graph_list_entities` with `blueprint: repository`) and show the person their titles. Then label each one that the domain owns or changes often. Use the entity's `name`, such as `gh-repo-123`, never `org/repo`, which is its `full_name` property.

```json
{"entities": [
  {"blueprint": "repository", "name": "<entity name>", "labels": {"team": ["<domain>"]}}
]}
```

A label key maps to a list of values. Labels merge per key: a key that you send replaces that key's values, and keys that you leave out are kept. When a repository already has `team: [checkout]` and this domain shares it, send `{"team": ["checkout", "<domain>"]}`.

A repository that the Context Graph does not have yet (no import from that code host) cannot be labelled. Record it in `<domain>-codebase` and say in the report that an import of the code host would add it.

## 4. Notification channels

The alert notifications for a team go to the channels in its `notification_channels` property. Only Slack channels can go there. Read the team first: the property is replaced whole, so send the full list, the existing channels included.

```json
{"entities": [
  {"blueprint": "team", "name": "<domain>",
   "properties": {"notification_channels": [
     {"provider": "slack", "channel_id": "<C…>", "channel_name": "<name>", "integration_id": "<Slack integration id>"}
   ]}}
]}
```

Get `channel_id` from the Slack integration's tools, not from the person. `integration_id` is required when the organization has more than one Slack workspace: ask which one if there is doubt. Channels in other chat tools go in the architecture skill.

## Label keys are shared

Labels belong to the whole organization. The first time any entity or skill uses a key (`team`, `service`), the key becomes available on every entity and skill in the organization. Before you write a key that no entity has yet, say so in one line. To check whether a key exists, list entities with that key and any value: `context_graph_list_entities` with `labels: {"team": []}` and `limit: 1`.

The skills that onboarding writes carry their labels in their frontmatter (`- team: <domain>`, `- service: <name>`). Use the same values, byte for byte, as on the entities: that is what links a skill to the team and the service in the graph.
