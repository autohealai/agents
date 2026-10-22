---
id: hypothesis
name: Hypothesis
description: "One candidate root cause of an incident: the claim, the causal chain and evidence that supports it, the reviewer's verdict, and the fixes it implies."
format: application/json
---

One artifact per candidate root cause, revised in place as the work proceeds rather than superseded by a second artifact.

Four writers own four disjoint parts, and each leaves the others alone:

- The planner creates it with slug, name, description, mechanism and status "proposed", plus its orientation (category, prior_confidence, supporting_signals, investigate_by).
- The investigator fills in causal_chain, confidence, investigation_summary and sets status to "investigated" — or "withdrawn" if the evidence kills it. It never writes review or mitigations.
- The reviewer writes review, and nothing else. A verdict that edits the claim it is judging is not a review.
- The fix planner writes mitigations, and nothing else.

Every evidence_id is copied verbatim from an <evidence id="#ev-..."/> tag that followed a tool result in your own run. An id you did not see is not evidence.

Prefer few strong steps to many weak ones: a causal chain is capped at five, and a step without evidence is an assertion.
