# Incident Response

Investigates a production incident end to end: gathers evidence, commits to a root-cause conclusion recorded as an artifact, has it adversarially verified, reworks it if the verdict says so, and reports the cause with its evidence and a proposed mitigation.

It weighs the competing explanations in one context and commits to one, rather than investigating each in parallel. The conclusion goes into a `hypothesis` artifact: a causal chain of at most five steps, the evidence and known gaps of each step, and what it ruled out. Its private child, `incident-verifier`, then tries to disprove that record in a fresh session and writes its verdict onto it as `review`. The lead reworks the conclusion at most twice when the verdict rejects it or finds it incomplete, writes the write-up and proposed mitigations into the record, and returns `root_cause`, a `confidence` label (Confirmed, Likely, Possible or Speculative), the record's id and, when a person must answer something first, `needs_human_input`.

## Files

```
agents/incident-response/
  agent.yaml
  agents/incident-verifier/agent.yaml
  agents/incident-verifier/instructions.md
  artifact-templates/hypothesis/TEMPLATE.md
  artifact-templates/hypothesis/renderer.liquid
  artifact-templates/hypothesis/schema.json
  catalog.yaml
  evals/causal-chain-completeness.yaml
  evals/evidence-grounding.yaml
  evals/hypothesis-verification.yaml
  evals/mitigation-safety.yaml
  evals/root-cause-correctness.yaml
  instructions.md
  skills/deploy-correlation/SKILL.md
  skills/retry-storm-diagnosis/SKILL.md
  skills/rollback-verification/SKILL.md
```

Every agent here uses the `apiVersion: agents.autoheal.ai/v1` format.
The agent lists no `skills`, so it gets the skills in its own `skills/` folder and every skill in your project: your team's runbooks and procedures reach it too. Evals are private to the agent, so its references use `./` (`./evals:<name>`). The `hypothesis` artifact template is not: both agents name it as `hypothesis`, the project's template, because a child agent cannot name its parent's templates.

## Use it

1. In Autoheal, create an agent named `incident-response` and paste [`agent.yaml`](agent.yaml) into its editor.
2. In the agent's file tree, create `instructions.md` and paste [`instructions.md`](instructions.md) into it.
3. Create the private child agent at the same path and paste its files in: `agents/incident-verifier/`. The lead calls it as `./agents:incident-verifier`, so the path must match.
4. Copy the `skills/` and `evals/` folders into the agent's file tree at the same paths.
5. Put the `hypothesis` template at the project's `artifact-templates/hypothesis/`, at the top of the project rather than inside the agent's folder, and paste the three files from [`artifact-templates/hypothesis/`](artifact-templates/hypothesis/) into it.
6. Connect the integrations it reads from: logs, metrics and traces, deploy and config history, and your code host. It uses whatever is connected.
7. Run it once by hand and read what it returns before adding a trigger.

## Safety

It only reads your systems. The one thing it writes is its own `hypothesis` record in Autoheal. It never creates, changes, restarts or deletes a live resource; its mitigations are proposals for the responder.
