# GCP AI Cost Weekly

Posts a weekly ESTIMATE of your GCP Vertex AI LLM spend to a Slack channel, broken
down by model, with the week-over-week change. The estimate is Cloud Monitoring token
metrics × model list price — not your invoiced bill.

## Use it
1. Copy `agent.yaml` into a new agent in Autoheal, and pick any model to run it.
2. Replace `#YOUR_COST_CHANNEL` (in the instructions) with your Slack channel.
3. In **STEP G2**, set `PROJECTS="..."` to the GCP project IDs you want to report on.
4. Edit the **STEP G3** pricing block: list the models your projects serve and your
   own $/MTok rates. The example rows just show the shape.
5. Connect the Slack integration and a read-only GCP integration whose service
   account has `roles/monitoring.viewer` on every project you report on.
6. Schedule it to run weekly.

## Needs
- A Slack integration and a channel to post to. The agent already requests Slack
  write access via its `capabilities` block — you just connect the integration.
- A GCP integration whose service account has `roles/monitoring.viewer` on each
  project, with `gcloud` available in the run environment.
- Your model list prices — kept in the STEP G3 block; update them as prices change.

## Note
The channel and project list are intentionally placeholders and no credentials are
stored in the file: you supply the channel, the projects, and connect the integration.
The numbers are estimates, not invoiced dollars.
