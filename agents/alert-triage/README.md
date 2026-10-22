# Alert Triage

When a new alert group fires, links the alerts that fired alongside it through the service dependency graph and pages the owner of the cause once. Flags noisy monitors and proposes a threshold change.

## Files

```
agents/alert-triage/
  agent.yaml
  catalog.yaml
  evals/page-routing-accuracy.yaml
  evals/root-cause-grouping.yaml
  instructions.md
  skills/co-firing-correlation/SKILL.md
```

Every agent here uses the `apiVersion: agents.autoheal.ai/v1` format.
Skills and evals are private to the agent, so its references use `./` (`./skills:<name>`, `./evals:<name>`).

## Use it

1. In Autoheal, create an agent named `alert-triage` and paste [`agent.yaml`](agent.yaml) into its editor.
2. In the agent's file tree, create `instructions.md` and paste [`instructions.md`](instructions.md) into it.
3. Copy the `skills/` and `evals/` folders into the agent's file tree at the same paths.
4. Connect the integrations it reads from, and grant write access to PagerDuty and Datadog.
5. Run it once by hand and read what it returns before adding a trigger.

## Safety

It posts messages and comments. It never changes code or infrastructure.
