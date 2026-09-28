# Azure AI Cost Weekly

Posts a weekly ESTIMATE of your Azure AI (Foundry / Azure OpenAI) LLM spend to a
Slack channel, broken down by model, with the week-over-week change. The estimate
is Azure Monitor token metrics × model list price — not your invoiced bill.

## Use it
1. Copy `agent.yaml` into a new agent in Autoheal.
2. In the instructions, replace `#YOUR_COST_CHANNEL` with your Slack channel.
3. Connect the Slack integration and a read-only Azure identity (Reader role).
4. Schedule it to run weekly.

## Needs
- A Slack integration and a channel to post to.
- Read-only Azure access (an identity with the Reader role), with `az` available in
  the run environment.
- Model list prices — kept in the instructions; update them as prices change.

## Note
The channel is intentionally a placeholder (`#YOUR_COST_CHANNEL`) and no credentials
are stored in the file: you supply the channel and connect the integration. The
numbers are estimates, not invoiced dollars.
