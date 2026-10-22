# Incident Response

Investigates a production incident end to end: gathers evidence from the connected observability and deployment sources, tests competing explanations through its own subagents, and proposes a bounded mitigation.

## Files

```
agents/incident-response/
  agent.yaml
  agents/adversarial-verifier/agent.yaml
  agents/adversarial-verifier/instructions.md
  agents/hypothesis-investigator/agent.yaml
  agents/hypothesis-investigator/instructions.md
  artifact-templates/hypothesis/TEMPLATE.md
  artifact-templates/hypothesis/renderer.liquid
  artifact-templates/hypothesis/schema.json
  catalog.yaml
  evals/causal-chain-completeness.yaml
  evals/evidence-grounding.yaml
  evals/hypothesis-verification.yaml
  evals/mitigation-safety.yaml
  evals/root-cause-correctness.yaml
  evals/severity-calibration.yaml
  instructions.md
  prompts/causal-chain.md
  skills/deploy-correlation/SKILL.md
  skills/retry-storm-diagnosis/SKILL.md
  skills/rollback-verification/SKILL.md
```

Every agent here uses the `apiVersion: agents.autoheal.ai/v1` format.
Skills, evals and the artifact template are private to the agent, so its references use `./` (`./skills:<name>`, `./evals:<name>`) and child agents reach the parent's skills with `../skills:<name>`.

## Use it

1. In Autoheal, create an agent named `incident-response` and paste [`agent.yaml`](agent.yaml) into its editor.
2. In the agent's file tree, create `instructions.md` and paste [`instructions.md`](instructions.md) into it.
3. Create each private child agent at the same path and paste its files in: `agents/adversarial-verifier/`, `agents/hypothesis-investigator/`. The parent calls them as `./agents:<name>`, so the paths must match.
4. Copy the `prompts/`, `skills/`, `evals/` and `artifact-templates/` folders into the agent's file tree at the same paths.
5. Connect the integrations it reads from.
6. Replace the placeholders listed below.
7. Run it once by hand and read what it returns before adding a trigger.

## Placeholders

- `#ev-`: the Slack channel it posts to. Use your own.
- `#ev-11`: the Slack channel it posts to. Use your own.
- `#ev-2`: the Slack channel it posts to. Use your own.
- `#ev-4`: the Slack channel it posts to. Use your own.
- `#ev-7`: the Slack channel it posts to. Use your own.
- `#ev-9`: the Slack channel it posts to. Use your own.

## Safety

It only reads. It never creates, changes or deletes anything.
