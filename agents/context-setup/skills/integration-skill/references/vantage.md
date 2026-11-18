# Vantage

What the Vantage skill must tell agents about this customer's cost data. Agents use it to root-cause cost anomalies, then pivot to the cloud provider's own tools to find the workload behind the spend. Record what is true only here.

## Capture

- **Workspaces:** each workspace's name and token. With more than one, agents must pass `workspace_token` to `vantage_get_costs`, `vantage_list_cost_providers` and `vantage_list_cost_services`.
- **Providers and services:** the providers in use and, for each, the services that carry most spend, under the exact names Vantage uses (`aws`: `AmazonEC2`, `AmazonRDS`; `gcp`: `Compute Engine`, `BigQuery`).
- **Cost reports:** the reports to pull first when an anomaly fires, with name, token and what each covers (Checkout prod: AWS account `123456789012`, tag `team:checkout`).
- **Watched anomalies:** the provider and service pairs the team watches, and who owns each.
- **Ownership tags:** the tag keys that map spend to teams, services or environments (`team`, `service`, `env`), which agents use as `groupings=tag:<key>`.
- **Accounts:** the cloud accounts or projects that matter and what runs in each (`123456789012` = prod; `acme-data` = data platform).
- **Severity and currency:** the dollar impact the person calls critical, and the billing currency of each report.
- **How anomalies arrive:** Jira relay, Slack mention or a direct ask. For Jira, the project and where the `anml_...` token sits in the ticket.
- **Pivot:** for each provider, the Autoheal integration or CLI agents use to inspect a resource (`aws`, `gcloud`, `kubectl`), and the label or tag that ties a resource to a workload.
- **Queries that ran:** each VQL filter written into the skill, with the window it ran on.

## Ask the person

- Which services or accounts must never spike unnoticed, and who owns them?
- What dollar impact makes an anomaly critical for them?
- Which tag keys map spend to teams or services, and are they applied everywhere?

## Explore

- `vantage_test_connection`, then `vantage_list_workspaces`.
- Reports: `vantage_list_cost_reports` with `limit=50`.
- Providers and services: `vantage_list_cost_providers`, then `vantage_list_cost_services` with `provider=<each>`.
- Anomalies: `vantage_list_anomaly_alerts` with `start_date` 30 days ago and `limit=25`, to see which provider and service pairs fire; `vantage_get_anomaly_alert` on one, for its `resources`.
- Recommendations: `vantage_list_recommendations` with `limit=25`, for the categories in use.
- Filters and tags: one `vantage_get_costs` call per report or VQL filter you will write down, over 7 days with `date_bin=day`; use `groupings=tag:<key>` to confirm a tag key carries spend.

## Guardrails

Write the ones agents will hit into the skill.

- `vantage_get_costs` needs `cost_report_token` or `vql_filter`. Always pass `start_date` and `end_date` (`YYYY-MM-DD`); without them it reads 30 days.
- `vantage_get_costs` refuses a response over 180 KB with an error; it does not truncate. Narrow the window, use a coarser `date_bin` (`week`, `month`), or drop groupings. `groupings=resource_id` over weeks hits this.
- `date_bin` takes `hour`, `day`, `week`, `month` or `quarter`. `groupings` takes `account_id`, `billing_account_id`, `charge_type`, `cost_category`, `cost_subcategory`, `provider`, `region`, `resource_id`, `service`, `tagged` or `tag:<key>`; anything else is rejected.
- `limit` is at most 500 on `vantage_get_costs` and 200 on the list tools.
- When a VQL filter returns an empty `costs` array, check its provider and service names against `vantage_list_cost_services` before concluding there was no spend.
- Amounts are strings in the report's currency. Do not compare amounts across reports in different currencies.

## Pitfalls

- Cost report tokens and anomaly tokens look alike. Pass each only to the parameter its source field names.
- An anomaly with no `previous_amount` is a new service or workload. Check whether it was intended before treating it as an incident.
- Budgets has no tool: say so in the Budgets row's `agent_findings`.
- `anomaly_providers_services` is the customer's watchlist: do not add rows. Put the provider and service menu you found in the Anomaly Alerts row's `agent_findings`.
- Add a `cost_reports_important` or `recommendation_categories` row only when the choice is clear (the only report, a category that dominates). `anomaly_dollar_threshold` is the person's.
- Do not pull cost rows to fill the form: figures go stale. Call `vantage_get_costs` only to confirm a filter you will write down.

## Leave out

VQL syntax, Vantage's data model, cost figures and anomaly lists, and providers the customer does not use.
