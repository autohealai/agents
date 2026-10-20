# Move a customer from their POV install to a new install

This tool copies a customer's skills, memories and past investigations from their old POV install into a new install.

- **Skills**: integration guides, Architecture Overview and custom skills become Git skills in one project.
- **Memories**: an LLM rewrites each one into the new format (Use when / What to do / Avoid when). A person checks them before they go in.
- **Investigations**: copied as hidden history. They don't show in lists but open by link.

Not moved: integrations, chats, profiles, attachments, and the Investigation Steps section (paste that into the agent's instructions by hand).

## Before you start

1. **Get the old data.** Ask whoever runs the old install for this dump, then restore it into a Postgres the new install can reach:

   ```bash
   pg_dump -Fc -d agents -t investigations -t hypotheses -t agent_sessions -t agent_session_messages -t tool_calls -t feedbacks -t experiments -t ekb_tactical_memories -t agentsmd_sections -t agentsmd_latest_sections -t runbooks -t runbooks_latest -t alembic_version -f agents.dump
   ```

2. **Make a pod to run it in**, a copy of the agents-py worker that does nothing else:

   ```bash
   kubectl debug <worker-pod> -n <namespace> --copy-to=pov-migration --container=agents-py-worker --profile=restricted --keep-labels=false --keep-liveness=false --keep-readiness=false --keep-startup=false -- sleep 86400
   ```

   Copy this folder into the pod's `/tmp`. Delete the pod when you are done.

3. **Collect**: the target tenant id and project id, a login token from the new install saved to a file (it lasts 12 hours), and the customer's label map if they have one (see `label-maps/`).

4. **Take a database snapshot** of the new install, so you can roll back.

## Run it

```bash
python migrate.py migrate-all \
  --bundle /tmp/migration \
  --source-db postgresql://user:pass@host/olddb \
  --tenant <tenant-id> --project <project-id> \
  --domain <new-install-domain> --token-file /tmp/token \
  --label-map label-maps/<customer>.json
```

It writes to the new install's database using the pod's own settings, and to the app using the token.

It runs twice:

1. **First run** exports the old data, rewrites the memories and stops. Open `/tmp/migration/review.html` and read the new memories.
   - Some are **held** because the LLM added details that weren't in the original. Keep one as it is with `python migrate.py accept-memories --bundle /tmp/migration --ids <first 8 characters>`, or leave it out.
2. **Second run**: the same command with `--reviewed` added. It checks everything first and writes nothing if a check fails. Then it moves skills, memories, labels and investigations, and checks each one landed.

Then look at the Skills page, the Memories page and one investigation link in the app.

**If it stops**, fix what it says and run the same command again. It picks up where it left off and never copies anything twice.

Tips:
- Start it in the background so a dropped connection doesn't kill it: `setsid nohup python -u migrate.py ... > log 2>&1 &`.
- `--skip investigations` (or `skills`, `memories`, `labels`) leaves a part out.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Done (or paused for review on the first run) |
| 1 | Some items failed and the rest went in. The output says which and why |
| 2 | Stopped before writing anything, for example a project the token can't see |
| 3 | Lost the database or the app partway. Run the same command again |

## Undo

Run these in order:

```bash
python migrate.py unlabel-memories --bundle /tmp/migration --project <project-id> --domain <new-install-domain> --token-file /tmp/token
python migrate.py undo-memories --bundle /tmp/migration --tenant <tenant-id> --project <project-id>
python migrate.py undo-investigations --bundle /tmp/migration --tenant <tenant-id> --project <project-id>
```

Then delete the skills in the Skills page. If anything else looks wrong, restore the snapshot.

## Good to know

- Old user ids are kept, so "accepted by" can show an unknown user. Pass `--user-map` (a CSV of `old_user_id,new_user_id`) to fix that.
- The built-in Architecture Overview shows "Needs curation". The text is in the Architecture Overview Git skill instead.
- Every step also runs on its own. `python migrate.py --help` lists them all.
