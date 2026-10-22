# Release Readiness

Reads a release candidate and its change diff, checks migrations, canary and rollback plan through its own subagents, and returns a ship-or-hold verdict with the blocking risks and the team that owns each one.

## Files

```
agents/release-readiness/
  agent.yaml
  agents/canary-evidence-auditor/agent.yaml
  agents/canary-evidence-auditor/instructions.md
  agents/migration-safety-analyst/agent.yaml
  agents/migration-safety-analyst/instructions.md
  catalog.yaml
  evals/canary-validity.yaml
  evals/gate-coverage.yaml
  evals/hold-justification.yaml
  evals/owner-attribution.yaml
  evals/risk-evidence-grounding.yaml
  evals/verdict-correctness.yaml
  instructions.md
  prompts/gate-report.md
  skills/canary-coverage/SKILL.md
  skills/migration-reversibility/SKILL.md
```

Every agent here uses the `apiVersion: agents.autoheal.ai/v1` format.
Skills and evals are private to the agent, so its references use `./` (`./skills:<name>`, `./evals:<name>`) and child agents reach the parent's skills with `../skills:<name>`.

## Use it

1. In Autoheal, create an agent named `release-readiness` and paste [`agent.yaml`](agent.yaml) into its editor.
2. In the agent's file tree, create `instructions.md` and paste [`instructions.md`](instructions.md) into it.
3. Create each private child agent at the same path and paste its files in: `agents/canary-evidence-auditor/`, `agents/migration-safety-analyst/`. The parent calls them as `./agents:<name>`, so the paths must match.
4. Copy the `prompts/`, `skills/` and `evals/` folders into the agent's file tree at the same paths.
5. Connect the integrations it reads from.
6. Replace the placeholders listed below.
7. Run it once by hand and read what it returns before adding a trigger.

## Placeholders

- `#ev-`: the Slack channel it posts to. Use your own.

## Safety

It only reads. It never creates, changes or deletes anything.
