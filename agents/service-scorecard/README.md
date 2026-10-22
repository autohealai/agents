# Service Scorecard

Every week, checks each service against the platform team's scorecard (on-call, SLO, monitors, runbook and so on). For a failing rule it opens a pull request in the owning repository, with SLO targets taken from the service's own 28-day history, and closes the ticket once the rule passes.

## Files

```
agents/service-scorecard/
  agent.yaml
  catalog.yaml
  evals/scorecard-fix-actionability.yaml
  evals/slo-target-grounding.yaml
  instructions.md
  skills/slo-from-history/SKILL.md
```

Every agent here uses the `apiVersion: agents.autoheal.ai/v1` format.
Skills and evals are private to the agent, so its references use `./` (`./skills:<name>`, `./evals:<name>`).

## Use it

1. In Autoheal, create an agent named `service-scorecard` and paste [`agent.yaml`](agent.yaml) into its editor.
2. In the agent's file tree, create `instructions.md` and paste [`instructions.md`](instructions.md) into it.
3. Copy the `skills/` and `evals/` folders into the agent's file tree at the same paths.
4. Connect the integrations it reads from, and grant write access to GitHub and Jira.
5. Run it once by hand and read what it returns before adding a trigger.

## Safety

It opens pull requests, issues or tickets for a human to review. It never merges or deploys.
