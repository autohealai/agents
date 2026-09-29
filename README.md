# Autoheal Agents

A public library of ready-to-run agents for the [Autoheal](https://autoheal.ai) platform.

Each agent is a single `agent.yaml` you can **copy and paste into the Autoheal agent
editor** to get running in seconds. Browse the folders below, open an agent's
`agent.yaml`, copy it, and paste it into a new agent in the product.

Agents here come from both the Autoheal team and the Autoheal community — anyone can
[contribute one](CONTRIBUTING.md) by opening a pull request.

## Agents

| Agent | What it does |
|-------|--------------|
| [`azure-ai-cost-weekly`](agents/azure-ai-cost-weekly/) | Posts a weekly estimate of Azure AI (Foundry / Azure OpenAI) LLM spend to a Slack channel, broken down by model. |
| [`gcp-ai-cost-weekly`](agents/gcp-ai-cost-weekly/) | Posts a weekly estimate of GCP Vertex AI LLM spend to a Slack channel, broken down by model. |
| [`aws-ai-cost-weekly`](agents/aws-ai-cost-weekly/) | Posts a weekly AWS Bedrock/Claude LLM cost report (all accounts) to a Slack channel, with week-over-week change. |

## How to use an agent

1. Open the agent's folder and its `agent.yaml`.
2. Copy the file contents.
3. In Autoheal, create a new agent and paste the YAML into the editor.
4. Replace any placeholders (e.g. the Slack channel), connect the integrations the
   agent references, then save and run.

## Repo layout

```
agents/
  <agent-name>/
    agent.yaml     # the agent spec — copy this into the editor
    README.md      # what the agent does and what it needs
```

## Contributing

Anyone can add an agent — Autoheal or an Autoheal customer. Open a pull request
with a folder under `agents/<agent-name>/` containing an `agent.yaml` and a short
`README.md`. CI validates every agent and a maintainer reviews before merge. See
[CONTRIBUTING.md](CONTRIBUTING.md) for the format and the rules (keep it generic,
no secrets, no tenant-specific IDs).

Licensed under [MIT](LICENSE).
