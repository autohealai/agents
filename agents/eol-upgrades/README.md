# EOL Upgrades

Upgrades every repository in a migration off an end-of-life runtime, toolchain or base image. Tests the upgrade steps on one pilot repository per language first, then opens the rest tier by tier once the platform lead approves. A repository counts as done when production runs the new image.

## Files

```
agents/eol-upgrades/
  agent.yaml
  catalog.yaml
  evals/migration-pilot-discipline.yaml
  evals/migration-pr-readiness.yaml
  instructions.md
  skills/fleet-migration-playbook/SKILL.md
```

Every agent here uses the `apiVersion: agents.autoheal.ai/v1` format.
Skills and evals are private to the agent, so its references use `./` (`./skills:<name>`, `./evals:<name>`).

## Use it

1. In Autoheal, create an agent named `eol-upgrades` and paste [`agent.yaml`](agent.yaml) into its editor.
2. In the agent's file tree, create `instructions.md` and paste [`instructions.md`](instructions.md) into it.
3. Copy the `skills/` and `evals/` folders into the agent's file tree at the same paths.
4. Connect the integrations it reads from, and grant write access to GitHub, Jira and Slack.
5. Replace the placeholders listed below.
6. Run it once by hand and read what it returns before adding a trigger.

## Placeholders

- `<org>`: your GitHub organisation.
- `<prod-namespace>`: the Kubernetes namespace your production services run in.

## Safety

It opens pull requests, issues or tickets for a human to review. It never merges or deploys.
