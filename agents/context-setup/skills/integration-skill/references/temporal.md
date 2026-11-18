# Temporal

What the Temporal skill must tell agents about this customer's Temporal. Agents already know the `temporal` CLI and the visibility query language; record what is true only here. There are no Temporal MCP tools: explore with the `temporal` CLI through `bash`.

## Capture

- **Server:** Temporal Cloud or self-hosted, and the server version. Cloud restricts some `operator` commands, so state it first.
- **Connections:** each connection's namespace (on Cloud `<namespace>.<account_id>`, `prod.o3ya3`), its address, and the environment it serves. With several connections, agents pass `--namespace` and `--address` on every command.
- **Namespaces:** each one agents use, its environment, and its retention period (closed workflows older than that are gone).
- **Workflow types:** the critical ones, what each does, its normal duration, and the task queue it runs on (`OrderWorkflow` on `orders-tq` usually closes in 2 minutes).
- **Workflow ids:** how ids are built (`order-<orderId>`), so agents go from a customer's order id straight to `temporal workflow describe --workflow-id order-123`.
- **Task queues:** each queue that matters, the worker deployment that polls it (`orders-worker` in the `checkout` Kubernetes namespace), and whether it serves workflow tasks, activity tasks or both.
- **Search attributes:** each custom attribute with its type and example values (`CustomerId`, Keyword, `cus_8812`), and which ones agents filter on.
- **Schedules:** the ones that matter, their cadence and what they start.
- **Failure patterns:** known failure modes with their error text (`ActivityTaskTimedOut` on `ChargeCard` when the payments API is slow), and which failures are expected retries.

## Ask the person

- Which workflow types matter most in an incident, and how long does each normally run?
- Which namespace is production?
- Which worker deployment polls each task queue, and where does it run?
- Which failures are known noise or expected retries?

## Explore

- Reachability first: `temporal workflow count`. If it returns `Unimplemented`, the server uses standard visibility: use `temporal workflow list --limit 1` and skip counts.
- Namespaces: `echo "$TEMPORAL_NAMESPACE"`, then `temporal operator namespace list -o json | jq -r '.[].namespaceInfo.name'` and `temporal operator namespace describe --namespace "$TEMPORAL_NAMESPACE"` for retention.
- Workflow types and their queues: `temporal workflow list --limit 200 -o json | jq -r '.[] | [.type.name, .taskQueue] | @tsv' | sort | uniq -c | sort -rn`.
- Workflow id conventions: `temporal workflow list --query "WorkflowType='<type>'" --limit 5 -o json | jq -r '.[].execution.workflowId'`.
- Search attributes: `temporal operator search-attribute list -o json`; read only the `customAttributes` object.
- Recent failures: get a boundary with `date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%SZ`, then `temporal workflow count --query "ExecutionStatus='Failed' AND CloseTime > '<since>'"`, and the same for `Terminated` and `TimedOut`. Long runners: `ExecutionStatus='Running' AND StartTime < '<since>'`.
- Task queues: `temporal task-queue describe --task-queue <name> --task-queue-type workflow`, and again with `activity`, for pollers and backlog.
- Schedules: `temporal schedule list -o json | jq '{count: length, sample: [.[0:20][] | .scheduleId]}'`, then `temporal schedule describe --schedule-id <id>` for one.
- Cluster: `temporal operator cluster health` and `temporal operator cluster describe` for the version.

## Guardrails

Write the ones agents will hit into the skill.

- Use only `list`, `count`, `describe` and `show`. Never `start`, `signal`, `terminate`, `cancel` or `reset`.
- Probe reachability with `temporal workflow count`, not `temporal operator cluster health`: Cloud can refuse `operator` commands, which reads as an outage when it is not.
- `tls: certificate required` proves the address was reached; the server wants a client certificate. With API-key auth, either the namespace does not allow API keys, or it allows both API keys and mTLS and needs the connection's Region set. Stop and report it; retrying does not help. `connection refused` on `127.0.0.1:7233` means the address is empty.
- There is no command that lists task queues: describe each by name, for both `workflow` and `activity` types.
- `temporal workflow show` can print a huge history. Run `describe` first, and filter `show -o json` with `jq` to the failed event.
- `temporal schedule list` prints every schedule: count it with `jq` instead.
- Each `bash` call is a new shell: compute a time boundary, then paste the printed value into the query.
- Bound failure counts by `CloseTime` and state the window; an unbounded count is all-time.

## Pitfalls

- A fresh form lists every feature unselected: that is "none selected". Probe each feature and note in each row's `agent_findings` whether it is reachable. Schedules and Cluster Health have no table: their counts and version go in `agent_findings` only.
- Fill `search_attributes` from `customAttributes` only, with the short type: `INDEXED_VALUE_TYPE_KEYWORD` is `Keyword`, and likewise `Int`, `Double`, `Bool`, `Datetime`, `Text`, `KeywordList`. `systemAttributes` are Temporal's built-ins.
- In `namespaces`, `workflow_types`, `task_queues` and `search_attributes`, fill `name` (and `type`) only; every `description` column and `failure_patterns` are the person's, so put what you learned about each into the skill.
- `-o json` field names differ between CLI versions. When a `jq` path returns nothing, print one record (`temporal workflow list --limit 1 -o json | jq '.[0]'`) and adjust.
- Visibility lags by a few seconds: a just-started workflow missing from `list` is not lost.

## Leave out

The visibility query syntax, the list of built-in search attributes, how workflows, activities and task queues work, CLI flags in general, and examples that do not use this customer's namespaces, workflow types or queues.
