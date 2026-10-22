# Cloud Cost Optimization

Starts from the bill rather than the resource list, attributes each of the largest lines to the service and team that caused it, and only then looks for what could change.

## Files

```
agents/cloud-cost-optimization/
  agent.yaml
  agents/savings-validator/agent.yaml
  agents/savings-validator/instructions.md
  agents/spend-attributor/agent.yaml
  agents/spend-attributor/instructions.md
  catalog.yaml
  evals/attribution-correctness.yaml
  evals/data-coverage-honesty.yaml
  evals/priority-agreement.yaml
  evals/recommendation-restraint.yaml
  evals/risk-statement-completeness.yaml
  evals/saving-accuracy.yaml
  instructions.md
  prompts/attribution.md
  skills/nat-gateway-attribution/SKILL.md
  skills/saving-risk-framing/SKILL.md
```

Every agent here uses the `apiVersion: agents.autoheal.ai/v1` format.
Skills and evals are private to the agent, so its references use `./` (`./skills:<name>`, `./evals:<name>`) and child agents reach the parent's skills with `../skills:<name>`.

## Use it

1. In Autoheal, create an agent named `cloud-cost-optimization` and paste [`agent.yaml`](agent.yaml) into its editor.
2. In the agent's file tree, create `instructions.md` and paste [`instructions.md`](instructions.md) into it.
3. Create each private child agent at the same path and paste its files in: `agents/savings-validator/`, `agents/spend-attributor/`. The parent calls them as `./agents:<name>`, so the paths must match.
4. Copy the `prompts/`, `skills/` and `evals/` folders into the agent's file tree at the same paths.
5. Connect the integrations it reads from.
6. Run it once by hand and read what it returns before adding a trigger.

## Safety

It only reads. It never creates, changes or deletes anything.
