# Incident Response

Investigates a production incident end to end and reports a root cause it has tried to disprove.
It gathers evidence from your connected integrations, commits to one conclusion with an explicit
causal chain, and hands that conclusion to a private **verifier** agent whose only job is to break
it. It reworks the conclusion when the verdict says so, then reports the cause with its evidence
and proposed mitigations. It only **reads**: it never creates, changes, restarts or deletes a live
resource.

## Files

```
agents/incident-response/
  agent.yaml                            # the lead agent
  agents/incident-verifier/agent.yaml   # its private verifier
  catalog.yaml                          # gallery fields only; not part of the agent
```

Both agents use the `apiVersion: agents.autoheal.ai/v1` format.

## What it does
1. **Plans** the investigation in its todo list: what the request says, which data sources to
   sweep, and what would tell competing explanations apart.
2. **Gathers** evidence. It starts from related earlier sessions of this agent, then takes a broad
   picture: deploys, config and flag changes, errors, key metrics, onset and blast radius. It
   searches approved memories whenever a concrete clue (an error code, a component) turns up.
3. **Commits to one conclusion.** It names two or three candidate mechanisms, picks the one the
   evidence best supports, and records it as a `hypothesis` artifact: a causal chain of at most
   five steps, the evidence for each step, each step's known gaps, and every rejected alternative
   with the evidence that ruled it out.
4. **Verifies.** It calls `incident-verifier` with the record's id, in a fresh session every time.
   The verifier classifies each step against its evidence, probes the declared gaps, runs its own
   falsification queries, calibrates confidence, and writes a `review` onto the record. It never
   edits the claim.
5. **Reworks** at most twice, when the review rejects the conclusion or asks for deeper work. If
   the verifier writes no review, it is called once more. With still no review, the conclusion is
   reported as unverified, at `Possible` confidence at most.
6. **Reports.** It writes the write-up and mitigations into the record and returns `root_cause`,
   `confidence` (Confirmed / Likely / Possible / Speculative), `hypothesis_artifact_id` and, when
   a human must answer something first, `needs_human_input`.

## Use it
1. In Autoheal, create an agent named `incident-response` and paste [`agent.yaml`](agent.yaml)
   into its editor.
2. In that agent's file tree, choose **New file**, create `agents/incident-verifier/agent.yaml`,
   and paste [`agents/incident-verifier/agent.yaml`](agents/incident-verifier/agent.yaml) into it.
   The lead calls the verifier as `./agents:incident-verifier`, so the path must match exactly.
   Until that file exists, the lead's subagent reference does not resolve.
3. Connect the integrations it should investigate with: observability (logs, metrics, traces),
   change tracking (deploys, feature flags) and your code host. It uses whatever is connected;
   more sources mean better evidence.
4. Run it with the incident in the prompt: the symptoms, the affected service and the time window.

## Model
Both agents ship with `claude-sonnet-5`: the lead at high thinking, the verifier at medium. To use
a different model your workspace offers, change `model.name` in both files.

## Needs
- At least one data source integration (see step 3). No single integration is required.
- The built-in `hypothesis` artifact template, which Autoheal provides. Nothing to create.

## Notes
- **Read-only.** Mitigations are proposals for the responder, never actions it takes.
- **One conclusion, adversarially checked.** It does not investigate competing hypotheses in
  parallel. It weighs them, commits to one, and records why it dropped the others. The verifier is
  the check on that choice.
- **No limits block.** It ships without `limits`, so a run uses the platform's default time limit.
- **Memory.** `memory: true` lets it search approved findings from past work. They are leads to
  verify, not facts.
