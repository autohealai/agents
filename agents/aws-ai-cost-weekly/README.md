# AWS AI Cost Weekly

Posts one weekly AWS Bedrock / Claude LLM cost report to a Slack channel, covering
every AWS account your integration exposes, with per-account and grand-total
week-over-week change. Unlike the Azure and GCP agents, these are **invoiced dollars**
from AWS Cost Explorer — not a token-price estimate — so there is no pricing table to
maintain.

## Use it
1. Copy `agent.yaml` into a new agent in Autoheal, and pick any model to run it.
2. Replace `#YOUR_COST_CHANNEL` (in the instructions) with your Slack channel.
3. (Optional) In **STEP W2**, adjust the service filter if you want more than
   Bedrock/Claude (e.g. include SageMaker).
4. Connect the Slack integration and an AWS integration that exposes the accounts you
   want reported.
5. Schedule it to run weekly.

## Needs
- A Slack integration and a channel to post to. The agent already requests Slack
  write access via its `capabilities` block — you just connect the integration.
- An AWS integration exposing one or more accounts, with `aws` available in the run
  environment. Each account's identity needs read access to Cost Explorer
  (`ce:GetCostAndUsage`) and `sts:GetCallerIdentity`; `iam:ListAccountAliases` is
  optional and only used for friendlier account labels (it falls back to the account
  ID without it).

## Note
The channel is intentionally a placeholder (`#YOUR_COST_CHANNEL`) and no credentials
or account IDs are stored in the file: accounts are discovered at run time from the
integration. The numbers are real invoiced costs from Cost Explorer.
