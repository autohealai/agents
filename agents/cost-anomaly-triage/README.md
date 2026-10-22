# Cost Anomaly Triage

For each daily Vantage cost anomaly, finds the deploy, config change, scaling event or traffic change that caused it, names the owning team, and proposes a fix with its dollar impact, as a pull request when the resource is declared in code.

## Files

```
agents/cost-anomaly-triage/
  agent.yaml
  catalog.yaml
  evals/anomaly-cause-correctness.yaml
  evals/spend-change-attribution.yaml
  instructions.md
  skills/cost-anomaly-attribution/SKILL.md
```

Every agent here uses the `apiVersion: agents.autoheal.ai/v1` format.
Skills and evals are private to the agent, so its references use `./` (`./skills:<name>`, `./evals:<name>`).

## Use it

1. In Autoheal, create an agent named `cost-anomaly-triage` and paste [`agent.yaml`](agent.yaml) into its editor.
2. In the agent's file tree, create `instructions.md` and paste [`instructions.md`](instructions.md) into it.
3. Copy the `skills/` and `evals/` folders into the agent's file tree at the same paths.
4. Connect the integrations it reads from, and grant write access to GitHub and Slack.
5. Replace the placeholders listed below.
6. Run it once by hand and read what it returns before adding a trigger.

## Placeholders

- `#finops`: the Slack channel it posts to. Use your own.

## Safety

It opens pull requests, issues or tickets for a human to review. It never merges or deploys.
