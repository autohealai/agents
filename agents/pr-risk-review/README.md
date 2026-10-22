# PR Risk Review

Reviews every pull request against main using the service's tier, incident history, SLO and production traffic, scores its risk from 0 to 100, picks reviewers from the catalog, and checks database migrations against the real table size and write rate.

## Files

```
agents/pr-risk-review/
  agent.yaml
  catalog.yaml
  evals/review-finding-accuracy.yaml
  evals/risk-context-grounding.yaml
  instructions.md
  skills/production-risk-scoring/SKILL.md
```

Every agent here uses the `apiVersion: agents.autoheal.ai/v1` format.
Skills and evals are private to the agent, so its references use `./` (`./skills:<name>`, `./evals:<name>`).

## Use it

1. In Autoheal, create an agent named `pr-risk-review` and paste [`agent.yaml`](agent.yaml) into its editor.
2. In the agent's file tree, create `instructions.md` and paste [`instructions.md`](instructions.md) into it.
3. Copy the `skills/` and `evals/` folders into the agent's file tree at the same paths.
4. Connect the integrations it reads from, and grant write access to GitHub and Slack.
5. Run it once by hand and read what it returns before adding a trigger.

## Safety

It posts messages and comments. It never changes code or infrastructure.
