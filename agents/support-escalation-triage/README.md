# Support Escalation Triage

When support escalates a Pylon ticket to engineering, replays the customer's own session, errors and logs, and matches them to a known issue by stack trace and release. Drafts the reply for support, or files a reproducible Jira bug to the owning team when the failure is new.

## Files

```
agents/support-escalation-triage/
  agent.yaml
  catalog.yaml
  evals/escalation-issue-match.yaml
  evals/escalation-repro-handoff.yaml
  instructions.md
  skills/escalation-triage/SKILL.md
```

Every agent here uses the `apiVersion: agents.autoheal.ai/v1` format.
Skills and evals are private to the agent, so its references use `./` (`./skills:<name>`, `./evals:<name>`).

## Use it

1. In Autoheal, create an agent named `support-escalation-triage` and paste [`agent.yaml`](agent.yaml) into its editor.
2. In the agent's file tree, create `instructions.md` and paste [`instructions.md`](instructions.md) into it.
3. Copy the `skills/` and `evals/` folders into the agent's file tree at the same paths.
4. Connect the integrations it reads from, and grant write access to Jira and Slack.
5. Replace the placeholders listed below.
6. Run it once by hand and read what it returns before adding a trigger.

## Placeholders

- `#support-escalations`: the Slack channel it posts to. Use your own.

## Safety

It opens pull requests, issues or tickets for a human to review. It never merges or deploys.
