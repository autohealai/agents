# PR Review Reminders

Keeps one Slack thread per open pull request in your organisation with its review status and who it is waiting on. Reminds only that person, reviewer or author, during their working hours, and suggests a reviewer from CODEOWNERS and the catalog when nobody was requested.

## Files

```
agents/pr-review-reminders/
  agent.yaml
  catalog.yaml
  evals/reminder-precision.yaml
  evals/review-reminder-fit.yaml
  instructions.md
  skills/review-turn-tracking/SKILL.md
```

Every agent here uses the `apiVersion: agents.autoheal.ai/v1` format.
Skills and evals are private to the agent, so its references use `./` (`./skills:<name>`, `./evals:<name>`).

## Use it

1. In Autoheal, create an agent named `pr-review-reminders` and paste [`agent.yaml`](agent.yaml) into its editor.
2. In the agent's file tree, create `instructions.md` and paste [`instructions.md`](instructions.md) into it.
3. Copy the `skills/` and `evals/` folders into the agent's file tree at the same paths.
4. Connect the integrations it reads from, and grant write access to Slack.
5. Replace the placeholders listed below.
6. Run it once by hand and read what it returns before adding a trigger.

## Placeholders

- `#pr-reviews`: the Slack channel it posts to. Use your own.

## Safety

It posts messages and comments. It never changes code or infrastructure.
