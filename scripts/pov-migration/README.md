# Move a customer from their POV install to a new install

This tool copies a customer's skills, memories and past investigations from their old POV install into a new install.

- **Skills**: integration guides, Architecture Overview and custom skills become Git skills in one project.
- **Memories**: an LLM rewrites each one into the new format (Use when / What to do / Avoid when). Accepted memories stay accepted, and memories waiting for review go to Needs review, as on the POV install.
- **Investigations**: copied as hidden history. They don't show in lists but open by link.

Not moved: integrations, chats, profiles, attachments, and the Investigation Steps section (paste that into the agent's instructions by hand).

## Before you start

1. **Dump the old database.** On the old install's host, run:

   ```bash
   docker exec postgres pg_dump -U postgres -Fc -d agents > agents.dump
   ```

2. **Load the dump into an empty database** on the new install's Postgres server. The tool reads the old data from there, not from the file. Run this from any machine that has the Postgres tools and can reach that server:

   ```bash
   createdb -h <postgres-host> -U <admin-user> pov_old
   pg_restore -h <postgres-host> -U <admin-user> -d pov_old --no-owner agents.dump
   ```

   If the server is only reachable from inside the cluster, run the same two commands in a throwaway Postgres pod:

   ```bash
   kubectl run pg-client -n <namespace> --image=postgres:16 -- sleep 86400
   kubectl cp agents.dump <namespace>/pg-client:/tmp/agents.dump
   kubectl exec -it -n <namespace> pg-client -- bash
   ```

   Delete that pod afterwards, and drop the `pov_old` database once the migration is done.

3. **Have ready**: the target tenant id and project id, the customer's label map if they have one (see `label-maps/`), and a login token from the new install saved in a file called `token`.

   To get the token, sign in to the new install as an admin, open the browser's developer tools, and copy the `Authorization` header of any `/api` request. It lasts 12 hours, so get it on the day you run the migration. An API key won't work: the Skills step only accepts a login token.

4. **Write down the time** just before you start. Azure backs up the new install's database continuously (7 days by default), so if something goes badly wrong you can restore it to that minute:

   ```bash
   az postgres flexible-server restore --resource-group <rg> --source-server <server> --name <new-server> --restore-time "<that time>"
   ```

   That's a last resort: it makes a new server, loses everything done after that time, and doesn't touch skills (they live in Git storage). For normal mistakes, use [Undo](#undo).

5. **Make a pod to run the tool in**, a copy of the agents-py worker that does nothing else, and copy the tool and the token into it:

   ```bash
   kubectl debug <worker-pod> -n <namespace> --copy-to=pov-migration --container=agents-py-worker --profile=restricted --keep-labels=false --keep-liveness=false --keep-readiness=false --keep-startup=false -- sleep 86400
   kubectl cp scripts/pov-migration <namespace>/pov-migration:/tmp/pov-migration
   kubectl cp token <namespace>/pov-migration:/tmp/token
   ```

   Delete the pod when you are done.

## Run it

Open a shell in the pod and start the migration:

```bash
kubectl exec -it -n <namespace> pov-migration -- bash
cd /tmp/pov-migration
python migrate.py migrate-all \
  --bundle /tmp/migration \
  --source-db postgresql://<admin-user>:<password>@<postgres-host>/pov_old \
  --tenant <tenant-id> --project <project-id> \
  --domain <new-install-domain> --token-file /tmp/token \
  --label-map label-maps/<customer>.json
```

It exports the old data, rewrites the memories, checks everything before writing, then moves skills, memories, labels and investigations and checks each one landed. It writes to the new install's database using the pod's own settings, and to the app using the token.

When it finishes, look at the Skills page, the Memories page and one investigation link in the app.

**If it stops**, fix what it says and run the same command again. It picks up where it left off and never copies anything twice.

Tips:
- Start it in the background so a dropped connection doesn't kill it: `setsid nohup python -u migrate.py ... > log 2>&1 &`.
- `--skip investigations` (or `skills`, `memories`, `labels`) leaves a part out.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Done |
| 1 | Some items failed and the rest went in, or the tool crashed. The output says which and why |
| 2 | Stopped before writing anything, for example a project the token can't see |
| 3 | Lost the database, the app or the model partway. Run the same command again |

## Undo

Run these in order:

```bash
python migrate.py unlabel-memories --bundle /tmp/migration --project <project-id> --domain <new-install-domain> --token-file /tmp/token
python migrate.py undo-memories --bundle /tmp/migration --tenant <tenant-id> --project <project-id>
python migrate.py undo-investigations --bundle /tmp/migration --tenant <tenant-id> --project <project-id>
```

Then delete the skills in the Skills page. If anything else looks wrong, restore the database to the time you wrote down.

## Good to know

- If the LLM's rewrite adds details the old memory never had, or doesn't fit the new format, the memory keeps its original text.
- Memories keep the date they were accepted, but not who accepted them: the old install's users don't exist on the new one.
- The tool needs a login token because the gateway doesn't accept API keys on the Git registry and project paths yet. Once it does, a service account key could replace the token.
- Every step also runs on its own. `python migrate.py --help` lists them all.
