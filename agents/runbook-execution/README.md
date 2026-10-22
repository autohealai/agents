# Runbook Execution

When a known alert fires, runs the approved runbook for it once, then checks recovery against the service's SLO for 15 minutes before resolving. If the service has not recovered, it escalates to on-call with a log of every action taken.

## Files

```
agents/runbook-execution/
  agent.yaml
  catalog.yaml
  evals/recovery-verification.yaml
  evals/runbook-outcome-correctness.yaml
  instructions.md
  skills/runbook-recovery-verification/SKILL.md
```

Every agent here uses the `apiVersion: agents.autoheal.ai/v1` format.
Skills and evals are private to the agent, so its references use `./` (`./skills:<name>`, `./evals:<name>`).

## Use it

1. In Autoheal, create an agent named `runbook-execution` and paste [`agent.yaml`](agent.yaml) into its editor.
2. In the agent's file tree, create `instructions.md` and paste [`instructions.md`](instructions.md) into it.
3. Copy the `skills/` and `evals/` folders into the agent's file tree at the same paths.
4. Connect the integrations it reads from, and grant write access to AWS, PagerDuty, Slack and Jira.
5. Replace the placeholders listed below.
6. Run it once by hand and read what it returns before adding a trigger.

## Placeholders

- `<org>`: your GitHub organisation.

## Safety

It takes the remediation steps in an approved runbook, so connect it only with the write access those steps need.
