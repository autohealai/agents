# Service Scaffolding

Creates a repository for a new-service request from the approved (golden-path) template, and checks it against the six scorecard rules before handing it over. Also opens pull requests that move older scaffolds to the current template.

## Files

```
agents/service-scaffolding/
  agent.yaml
  catalog.yaml
  evals/scaffold-handover-completeness.yaml
  evals/scorecard-pass-at-creation.yaml
  instructions.md
  skills/new-service-checklist/SKILL.md
```

Every agent here uses the `apiVersion: agents.autoheal.ai/v1` format.
Skills and evals are private to the agent, so its references use `./` (`./skills:<name>`, `./evals:<name>`).

## Use it

1. In Autoheal, create an agent named `service-scaffolding` and paste [`agent.yaml`](agent.yaml) into its editor.
2. In the agent's file tree, create `instructions.md` and paste [`instructions.md`](instructions.md) into it.
3. Copy the `skills/` and `evals/` folders into the agent's file tree at the same paths.
4. Connect the integrations it reads from, and grant write access to GitHub.
5. Replace the placeholders listed below.
6. Run it once by hand and read what it returns before adding a trigger.

## Placeholders

- `<org>`: your GitHub organisation.
- `<staging-namespace>`: the Kubernetes namespace your staging services run in.

## Safety

It opens pull requests, issues or tickets for a human to review. It never merges or deploys.
