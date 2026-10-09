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
3. Add a `metadata` block (recommended). It powers the catalog and the gallery —
   without it the agent still works but shows up with less detail. Place it
   anywhere at the top level (we put it just before `instructions`):
   ```yaml
   metadata:
     category: cost          # one of: sre, security, ci-cd, cost, code-review
     summary: "One short line for the card (falls back to description)."
     trigger: schedule       # manual | schedule
     safety: notify          # read-only | notify | propose
     requires:
       integrations: [aws, slack]   # integration type slugs the agent needs
   ```
   - `category` / `trigger` / `safety` are fixed sets — an invalid value fails CI.
     `safety`: `read-only` (reads only), `notify` (posts messages/comments only),
     `propose` (opens PRs/issues for a human to review — never merges or deploys).
   - `requires.integrations` are integration **type** slugs (e.g. `aws`, `github`,
     `slack`), not profile or account names. An unknown slug is a warning, not an
     error.
4. Add a short `README.md`: what it does and what integrations it needs.

### The `apiVersion` format

An agent may instead be written as `apiVersion: agents.autoheal.ai/v1`, the format
the agent editor now writes. The platform rejects any key that format does not
define, so it differs from the steps above:

- `agent.yaml` has `apiVersion: agents.autoheal.ai/v1`, `name` (equal to the folder
  name), `description`, `model` and `instructions`, and no `schema_version`,
  `display_name`, `metadata`, `capabilities` or `model_settings`.
- The catalog fields go in `catalog.yaml` beside it: `display_name` plus the same
  keys as the `metadata` block (`category`, `summary`, `trigger`, `safety`,
  `requires`).
- Private child agents go at `agents/<child>/agent.yaml` inside the agent's folder,
  where the parent names them as `./agents:<child>`. Each is validated, and none
  is listed in the catalog on its own. Say in the README that the user must create
  them.
5. Keep it generic. No secrets, no API keys, and no tenant- or company-specific
   IDs (Slack channel IDs, account numbers, internal hostnames). Use a clearly
   named placeholder (e.g. `#YOUR_COST_CHANNEL`) and document it in the README.
6. Regenerate the catalog and commit it:
   ```bash
   pip install pyyaml
   python scripts/build_catalog.py   # rewrites catalog.json
   ```
   `catalog.json` is a **generated** index of every agent — do not hand-edit it.

CI runs `scripts/validate_agents.py` and rebuilds `catalog.json` on every PR; it
fails if the committed `catalog.json` is stale. A maintainer reviews before merge.
