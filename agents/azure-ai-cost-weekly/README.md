# Azure AI Cost Weekly

Posts a weekly ESTIMATE of your Azure AI (Foundry / Azure OpenAI) LLM spend to a
Slack channel, broken down by model, with the week-over-week change. The estimate
is Azure Monitor token metrics × model list price — not your invoiced bill.

## Use it
1. Copy `agent.yaml` into a new agent in Autoheal, and pick any model to run it.
2. Replace `#YOUR_COST_CHANNEL` (in the instructions) with your Slack channel.
3. Edit the **STEP A3** pricing block: list the models your Azure account serves and
   your own $/MTok rates. The example rows just show the shape.
4. Connect the Slack integration and a read-only Azure identity (Reader role).
5. Schedule it to run weekly.

## Needs
- A Slack integration and a channel to post to. The agent already requests Slack
  write access via its `capabilities` block — you just connect the integration.
- Read-only Azure access (an identity with the Reader role), with `az` available in
  the run environment.
- Your model list prices — kept in the STEP A3 block; update them as prices change.

## Note
The channel is intentionally a placeholder (`#YOUR_COST_CHANNEL`) and no credentials
are stored in the file: you supply the channel and connect the integration. The
numbers are estimates, not invoiced dollars.
