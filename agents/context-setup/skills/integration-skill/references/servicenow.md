# ServiceNow

What the ServiceNow skill must tell agents about this customer's instance. Agents already know encoded-query syntax and the ITSM and CMDB data model; record what is true only here.

## Capture

- **Access:** the tables the account can read, and the ones that return 403. List the 403 tables so agents do not retry them.
- **Data the customer uses:** of CMDB, Incidents, Changes, Assignment Groups and Knowledge, the ones they rely on.
- **Scoping incidents to a service:** the field that ties an incident to a service here (`business_service`, `cmdb_ci`, `assignment_group` or `category`), with a query that ran (`business_service=Checkout^priority<=2^ORDERBYDESCopened_at`).
- **CMDB:** the CI classes that are populated and matter (`cmdb_ci_app_server`, `cmdb_ci_service_auto`), and the relationship types that carry blast radius (`Depends on::Used by`, `Runs on::Runs`).
- **Key services:** each important service's name, class table and `sys_id` (Checkout: `cmdb_ci_service`, `a1b2c3...`). The id saves agents a lookup before every `servicenow_get_ci_with_relations` call.
- **Coded values:** the stored value and label of incident `state`, `priority` and `category`, and of change `type`, `risk` and `state`, as this instance defines them (state `2` = In Progress; category `database`). Agents filter on stored values.
- **Custom fields:** the `u_*` fields on incidents and changes that carry meaning, with their values (`u_environment` = `prod`, `dr`; `u_customer_impact` = `true`).
- **Assignment groups:** the group that owns each important service, and the team behind it (`Payments SRE` owns Checkout).
- **Knowledge:** the knowledge bases and categories that hold runbooks and SOPs (`IT Operations` / `Runbooks`), and the filter that reaches them (`kb_knowledge_base=IT Operations^workflow_state=published`).
- **Writes:** whether agents may add work notes, or change state, assignment group or assignee with `servicenow_update_incident`, and on which incidents.

## Ask the person

- Which business services matter most in an incident, and which CIs or environments are production?
- Which assignment group owns each of those services, and who do agents escalate to?
- Which knowledge bases hold the runbooks the team trusts?
- Should agents write work notes or reassign incidents, or only read?

## Explore

- `servicenow_test_connection` first.
- Populated classes: `servicenow_aggregate` on `cmdb_ci` with `group_by=sys_class_name`. A class with no rows is not in use.
- Services: `servicenow_query_table` on `cmdb_ci_service` with `fields=name,sys_id,sys_class_name,operational_status`, `display_value=all` and `limit=50`.
- Topology: `servicenow_get_ci_with_relations` on one key service; note the relationship types in its inbound and outbound relations.
- Incident conventions: `servicenow_aggregate` on `incident` with `query=opened_at>=javascript:gs.daysAgoStart(30)` and `group_by` set in turn to `priority`, `state`, `category`, `assignment_group` and `business_service`.
- Incident fields: `servicenow_query_table` on `incident` with `order_by=-opened_at` and `limit=1` and no `fields`, to see every field, `u_*` included. Then sample ten with explicit `fields`.
- Coded values: `servicenow_query_table` on `sys_choice` with `query=name=incident^element=state` and `fields=value,label`; repeat for `priority`, `category`, and `change_request`'s `type`, `risk` and `state`. When `sys_choice` returns 403, take the values from the aggregates and ask the person what they mean.
- Assignment groups: `servicenow_query_table` on `sys_user_group` with `fields=name,description,manager,parent,active` and `limit=200`.
- Changes: `servicenow_aggregate` on `change_request` grouped by `type`, `risk`, then `state`.
- Knowledge: `servicenow_aggregate` on `kb_knowledge` with `query=workflow_state=published` and `group_by=kb_knowledge_base`, then `kb_category`.

## Guardrails

Write the ones agents will hit into the skill.

- Always pass `query`, `fields` and `limit` to `servicenow_query_table`. Unfiltered reads of `cmdb_ci`, `incident` or `sys_user` run past the 30-second timeout. `limit` is at most 1000.
- Count with `servicenow_aggregate`, never by paging rows.
- Encoded queries match stored values (`priority=1`, `state=2`), although results show labels by default.
- Reference fields (`cmdb_ci`, `assignment_group`, `business_service`) come back as names by default. To get a `sys_id` and the class table name for `servicenow_get_ci_with_relations`, read the record with `display_value=all`.
- `servicenow_update_incident` takes `sys_id`s for `assignment_group` and `assigned_to`, and the stored `state` value. Resolving or closing usually needs fields it cannot set, and ServiceNow rejects the update.
- A 403 means the account's role cannot read that table. Do not retry it.

## Pitfalls

- Do not filter `sys_user_group` on `active=true`: on least-privilege accounts it returns no rows, and the routing table comes out empty. Read all groups and treat a group as inactive only when `active` comes back `false`.
- `cmdb_relationship_notes`, `incident_scope_notes` and `knowledge_scope` are the person's fields: put what you found in the CMDB, Incidents and Knowledge rows' `agent_findings`.
- In `incident_field_glossary` and `change_field_glossary`, `field` and `values` are yours to fill and `meaning` is the person's: put the stored value with its label in `values` (`1 = Critical, 2 = High`).
- In `assignment_group_routing`, fill `group` only; `team` and `scope` are the person's.
- In `cmdb_classes`, add populated classes and key services as rows, with their row count and what they hold in `agent_findings`.

## Leave out

Encoded-query syntax, the ITSM and CMDB data model, what standard fields such as `opened_at` or `short_description` mean, live incident lists, and examples that do not use this customer's services, groups or classes.
