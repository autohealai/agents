# Coding Agent Spend

Every night, prices the coding agents' token usage by type, compares your repositories on cost per merged PR, and finds where each one's tokens go. It opens the fix as a PR: an ignore rule for the owning team, or a benchmarked settings change for platform engineering.

## Files

```
agents/coding-agent-spend/
  agent.yaml
  catalog.yaml
  evals/benchmarked-before-proposed.yaml
  evals/coding-spend-soundness.yaml
  instructions.md
  skills/coding-spend-attribution/SKILL.md
```

Every agent here uses the `apiVersion: agents.autoheal.ai/v1` format.
Skills and evals are private to the agent, so its references use `./` (`./skills:<name>`, `./evals:<name>`).

## Use it

1. In Autoheal, create an agent named `coding-agent-spend` and paste [`agent.yaml`](agent.yaml) into its editor.
2. In the agent's file tree, create `instructions.md` and paste [`instructions.md`](instructions.md) into it.
3. Copy the `skills/` and `evals/` folders into the agent's file tree at the same paths.
4. Connect the integrations it reads from, and grant write access to GitHub and Slack.
5. Replace the placeholders listed below.
6. Run it once by hand and read what it returns before adding a trigger.

## Placeholders

- `<org>`: your GitHub organisation.

## Safety

It opens pull requests, issues or tickets for a human to review. It never merges or deploys.
