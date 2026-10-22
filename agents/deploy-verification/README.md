# Deploy Verification

After each production deploy, compares error rate, latency and SLO burn with the pre-deploy baseline and the same hour last week. On a regression it can attribute to the change, it pages the owner and opens a revert PR.

## Files

```
agents/deploy-verification/
  agent.yaml
  catalog.yaml
  evals/deploy-verdict-correctness.yaml
  evals/regression-attribution.yaml
  instructions.md
  skills/deploy-regression-attribution/SKILL.md
```

Every agent here uses the `apiVersion: agents.autoheal.ai/v1` format.
Skills and evals are private to the agent, so its references use `./` (`./skills:<name>`, `./evals:<name>`).

## Use it

1. In Autoheal, create an agent named `deploy-verification` and paste [`agent.yaml`](agent.yaml) into its editor.
2. In the agent's file tree, create `instructions.md` and paste [`instructions.md`](instructions.md) into it.
3. Copy the `skills/` and `evals/` folders into the agent's file tree at the same paths.
4. Connect the integrations it reads from, and grant write access to PagerDuty and GitHub.
5. Run it once by hand and read what it returns before adding a trigger.

## Safety

It opens pull requests, issues or tickets for a human to review. It never merges or deploys.
