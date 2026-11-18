# Azure

What the Azure skill must tell agents about this customer's subscriptions. One identity often reads many subscriptions and none is a safe default, so the skill's core is the subscription map: which subscription is which, and what lives in each. Agents already know `az` and how to pick a subscription; record what is true only here.

## Capture

- **Subscription map:** each in-scope subscription's id, name and purpose (`Production — checkout and payments (AKS, Storage, Key Vault)`). The id is what agents pass to `--subscription`.
- **Per subscription:** its environment, the resource groups that hold production workloads, the dominant service types (AKS, App Service, SQL, Storage, Functions), and known recurring issues.
- **Low-signal subscriptions:** empty sandboxes and shared hubs (networking, identity) in one line each, so agents look elsewhere first.
- **Where telemetry lives:** the Log Analytics workspace ids that hold each environment's logs, and the Application Insights resources of the key services.
- **AKS:** each production cluster's name, resource group and the namespaces of the key services.
- **Connections:** when the project has two or more Azure connections, which subscriptions each one reads.

## Ask the person

- Which subscriptions are production, and which can agents ignore?
- Which services matter most in an incident, and where does each run (cluster, App Service, Function app)?
- Which Log Analytics workspace or Application Insights resource holds their logs?
- Which resource groups or subscriptions belong to which team?

## Explore

Run every command with the connection's config dir prefix that the `bash` result names (`AZURE_CONFIG_DIR=<dir> az ...`).

- Subscriptions: `az account list -o json` (`id`, `name`, `state`). When a recently granted one is missing, add `--refresh`.
- Per subscription: `az group list --subscription <id> --query "[].name" -o tsv` and `az resource list --subscription <id> --query "[].type" -o tsv | sort | uniq -c | sort -rn | head`.
- Across subscriptions: `az graph query -q "Resources | summarize count() by subscriptionId, type | top 50 by count_"`.
- Telemetry: `az monitor log-analytics workspace list --subscription <id> --query "[].{name:name,id:customerId,rg:resourceGroup}" -o table`.
- Clusters: `az aks list --subscription <id> --query "[].{name:name,rg:resourceGroup}" -o table`.

## Guardrails

Write the ones agents will hit into the skill.

- Pass `--subscription <id>` on every ARM command. Never run `az account set`: it changes the default for every later command of that connection.
- `az` reads are control-plane only (Reader): resource configuration, metrics, activity logs and Resource Graph. It cannot read blob contents, queue messages, database rows or Key Vault secret values.
- ARM read limits are per identity: keep sweeps bounded with `--query` and `head`, and filter by subscription.

## Pitfalls

- `az account list` returns nothing: the identity has no role yet, or a management-group grant has not propagated. Say so; do not invent rows.
- Skip subscriptions whose `state` is not `Enabled`.
- With dozens of subscriptions, draft purposes from names and look inside only the ones that hold production workloads.
- The form's `subscriptions` table: you fill `subscription_id` and `name`, and `purpose` only where it is blank. `selected` is the person's; when no row is selected, cover every Enabled subscription.

## Leave out

How `az` picks a subscription, `az` syntax, KQL syntax, and a live list of every resource: agents list live resources themselves.
