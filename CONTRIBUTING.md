# Contributing an agent

Add one agent per pull request.

1. Create `agents/<agent-name>/`, where `<agent-name>` is lowercase and matches
   `^[a-z0-9_-]+$`.
2. Add `agent.yaml` with these fields:
   - `schema_version: 1`
   - `name` — must equal the folder name
   - `display_name` — human-facing label
   - `description` — one or two sentences
   - `instructions` — the agent's prompt
   Leave `model` out; the platform fills it in.
3. Add a short `README.md`: what it does and what integrations it needs.
4. Keep it generic. No secrets, no API keys, and no tenant- or company-specific
   IDs (Slack channel IDs, account numbers, internal hostnames). Use a clearly
   named placeholder (e.g. `#YOUR_COST_CHANNEL`) and document it in the README.

CI runs `scripts/validate_agents.py` on every PR. A maintainer reviews before merge.
