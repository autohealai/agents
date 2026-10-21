"""Copy old investigations into a new install as hidden cold storage.

export-investigations  old agents DB -> a bundle folder: one JSON file per investigation + manifest.json
import-investigations  bundle -> new agents DB, one transaction per investigation, safe to rerun
verify-investigations  compare the target with the bundle
undo-investigations    delete exactly what the bundle names, for one tenant and project

Runs anywhere Python and asyncpg are, including an agents-py pod. With no --db,
it builds the connection from the pod's POSTGRES_CONFIG__* variables.
"""

import json
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from db import (
    RunStopped,
    Session,
    connect,
    outside_problem,
    require_columns,
    revision,
)

TABLES = [
    "investigations",
    "hypotheses",
    "agent_sessions",
    "agent_session_messages",
    "tool_calls",
    "feedbacks",
]
# Sessions a target worker could try to resume if they still looked live.
LIVE_SESSION_STATUSES = {"running", "waiting_for_input"}
# Import and undo share one claim, so they never run at the same time.
CLAIM = "pov-migration:investigations"
# What the export reads by name; anything else is copied as the source has it.
SOURCE_COLUMNS = {
    "investigations": [
        "id",
        "tenant_id",
        "is_shadow",
        "experiment_id",
        "archived",
        "parent_type",
        "is_running",
        "status",
    ],
    "hypotheses": ["investigation_id", "status", "status_changed_by", "created_at"],
    "agent_sessions": ["id", "parent_session_id", "agent_metadata", "created_at"],
    "agent_session_messages": ["id", "session_id", "artifact_ids"],
    "tool_calls": ["id", "session_id", "message_id"],
    "feedbacks": ["target_type", "target_id"],
}


# ---------------------------------------------------------------- export


async def session_trees(conn, inv_ids: list[str]) -> tuple[dict[str, list[str]], list[str]]:
    """Every transcript of each investigation, subagents included, plus orphans."""
    rows = await conn.fetch(
        "select id, parent_session_id, agent_metadata->>'investigation_id' as inv from agent_sessions"
    )
    children, by_id = defaultdict(list), {}
    for r in rows:
        by_id[r["id"]] = r
        if r["parent_session_id"]:
            children[r["parent_session_id"]].append(r["id"])
    orphans = [
        r["id"] for r in rows if r["parent_session_id"] and r["parent_session_id"] not in by_id
    ]

    trees = {}
    for inv in inv_ids:
        roots = [
            sid
            for sid, r in by_id.items()
            if sid == f"investigation-{inv}"
            or r["inv"] == inv
            or sid.startswith(f"autohealer-{inv}-")
        ]
        seen, stack = [], list(roots)
        while stack:
            sid = stack.pop()
            if sid in seen:
                continue
            seen.append(sid)
            stack.extend(children.get(sid, []))
        trees[inv] = seen
    return trees, orphans


async def pick_sample(conn, eligible: list[str], trees: dict[str, list[str]]) -> dict[str, str]:
    """One investigation per shape worth testing, keyed by the shape it covers."""
    msg_counts = {
        r["session_id"]: r["n"]
        for r in await conn.fetch(
            "select session_id, count(*) n from agent_session_messages group by 1"
        )
    }
    attach = {
        r["session_id"]
        for r in await conn.fetch(
            "select distinct session_id from agent_session_messages where cardinality(artifact_ids) > 0"
        )
    }
    size = {inv: sum(msg_counts.get(s, 0) for s in trees[inv]) for inv in eligible}
    inv = {
        str(r["id"]): r
        for r in await conn.fetch(
            "select * from investigations where id = any($1::uuid[])", eligible
        )
    }
    accepted = defaultdict(set)
    for r in await conn.fetch(
        "select investigation_id, status_changed_by from hypotheses where status = 'accepted' and investigation_id = any($1::uuid[])",
        eligible,
    ):
        who = "watcher" if r["status_changed_by"] == "ticket-outcome-watcher" else "person"
        accepted[who].add(str(r["investigation_id"]))

    def first(pred, key=None):
        cands = [i for i in eligible if pred(i)]
        return max(cands, key=key) if key and cands else (cands[0] if cands else None)

    shapes = {
        "largest transcript": first(lambda i: True, key=lambda i: size[i]),
        "most transcripts (subagents)": first(lambda i: True, key=lambda i: len(trees[i])),
        "has autohealer runs": first(lambda i: any(s.startswith("autohealer-") for s in trees[i])),
        "accepted by a person": first(lambda i: i in accepted["person"]),
        "accepted by ticket watcher": first(lambda i: i in accepted["watcher"]),
        "archived": first(lambda i: inv[i]["archived"]),
        "parent is a chat": first(lambda i: inv[i]["parent_type"] == "chat_session"),
        "parent is an alert group": first(lambda i: inv[i]["parent_type"] == "alert_group"),
        "has attachments": first(lambda i: any(s in attach for s in trees[i])),
        "still marked running": first(lambda i: inv[i]["is_running"]),
        "ended in error": first(lambda i: inv[i]["status"] == "error"),
        "smallest transcript": min(eligible, key=lambda i: size[i]) if eligible else None,
    }
    return {k: v for k, v in shapes.items() if v}


async def export(args):
    out = Path(args.out)
    if (out / "manifest.json").exists():
        sys.exit(f"{out} already holds an investigation export; use a fresh folder")
    (out / "investigations").mkdir(parents=True, exist_ok=True)
    conn = await connect(args.db)
    started = time.monotonic()
    try:
        await require_columns(conn, SOURCE_COLUMNS)
        all_inv = await conn.fetch("select id::text, is_shadow, experiment_id from investigations")
        excluded = {
            "shadow": [r["id"] for r in all_inv if r["is_shadow"]],
            "experiment": [r["id"] for r in all_inv if r["experiment_id"] and not r["is_shadow"]],
        }
        eligible = [r["id"] for r in all_inv if not r["is_shadow"] and not r["experiment_id"]]
        trees, orphans = await session_trees(conn, eligible)

        if args.select == "all":
            chosen, shapes = eligible, {}
        elif args.select == "sample":
            shapes = await pick_sample(conn, eligible, trees)
            chosen = list(dict.fromkeys(shapes.values()))
        else:
            chosen, shapes = [s.strip() for s in args.select.split(",") if s.strip()], {}
            unknown = set(chosen) - set(eligible)
            if unknown:
                sys.exit(f"not exportable (missing, shadow or experiment): {sorted(unknown)}")

        counts, nbytes, columns = defaultdict(int), defaultdict(int), {}
        for t in TABLES:
            columns[t] = [
                r["column_name"]
                for r in await conn.fetch(
                    "select column_name from information_schema.columns where table_name = $1 order by ordinal_position",
                    t,
                )
            ]
        for inv_id in chosen:
            sids = trees[inv_id]
            q = {
                "investigations": (
                    "select row_to_json(t)::text from investigations t where id = $1::uuid",
                    inv_id,
                ),
                "hypotheses": (
                    "select row_to_json(t)::text from hypotheses t where investigation_id = $1::uuid order by created_at",
                    inv_id,
                ),
                "agent_sessions": (
                    "select row_to_json(t)::text from agent_sessions t where id = any($1::text[]) order by created_at",
                    sids,
                ),
                "agent_session_messages": (
                    "select row_to_json(t)::text from agent_session_messages t where session_id = any($1::text[]) order by id",
                    sids,
                ),
                "tool_calls": (
                    "select row_to_json(t)::text from tool_calls t where session_id = any($1::text[]) order by id",
                    sids,
                ),
                "feedbacks": (
                    "select row_to_json(t)::text from feedbacks t where target_type = 'investigation' and target_id = $1::uuid",
                    inv_id,
                ),
            }
            doc = {}
            for t, (sql, param) in q.items():
                rows = [
                    json.loads(v)
                    for v in await conn.fetchval(
                        f"select coalesce(array_agg(x), '{{}}') from ({sql}) s(x)", param
                    )
                ]
                doc[t] = rows
                counts[t] += len(rows)
            blob = json.dumps(doc, separators=(",", ":"))
            (out / "investigations" / f"{inv_id}.json").write_text(blob)
            for t in TABLES:
                nbytes[t] += len(json.dumps(doc[t], separators=(",", ":")))

        manifest = {
            "created_at": datetime.now(UTC).isoformat(),
            "source_revision": await revision(conn),
            "source_tenants": sorted(
                {
                    r["tenant_id"]
                    for r in await conn.fetch("select distinct tenant_id from investigations")
                }
            ),
            "selection": args.select,
            "shapes": shapes,
            "investigation_ids": chosen,
            "session_ids": sorted({s for i in chosen for s in trees[i]}),
            "columns": columns,
            "counts": counts,
            "bytes": nbytes,
            "excluded": excluded,
            "orphan_sessions": orphans,
            "export_seconds": round(time.monotonic() - started, 1),
        }
        (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    finally:
        await conn.close()

    print(f"exported {len(chosen)} investigations to {out} in {manifest['export_seconds']}s")
    for t in TABLES:
        print(f"  {t:24} {counts[t]:>7} rows  {nbytes[t] / 1e6:8.1f} MB")
    for k, v in shapes.items():
        print(f"  sample: {k:30} {v}")
    print(
        f"  excluded: {len(excluded['shadow'])} shadow, {len(excluded['experiment'])} experiment; orphan sessions: {len(orphans)}"
    )


# ---------------------------------------------------------------- import


def check_ram_headroom(bundle: Path, todo: list[str]):
    """The largest investigation sets peak memory, at about 5x its file size (measured)."""
    if not todo:
        return
    biggest = max((bundle / "investigations" / f"{i}.json").stat().st_size for i in todo)
    need = 5 * biggest + 100 * 2**20
    print(
        f"  largest investigation {biggest / 2**20:.0f} MiB: expect ~{need / 2**20:.0f} MiB peak memory"
    )
    try:  # inside a container, compare with its memory limit
        limit = int(Path("/sys/fs/cgroup/memory.max").read_text())
        used = int(Path("/sys/fs/cgroup/memory.current").read_text())
    except (OSError, ValueError):
        return
    free = limit - used
    print(
        f"  container memory: {used / 2**20:.0f} of {limit / 2**20:.0f} MiB used, {free / 2**20:.0f} MiB free"
    )
    if need > 0.7 * free:
        print(
            "  WARNING: too close to the container's limit; run in a separate pod with more memory"
        )


class Transform:
    """The deliberate changes on the way in. Everything else, user ids included, is copied as is."""

    def __init__(self, tenant: str, project: str):
        self.tenant, self.project = tenant, project
        self.detached_parents = 0

    def apply(self, doc: dict) -> dict:
        inv = doc["investigations"][0]
        inv.update(tenant_id=self.tenant, project_id=self.project, is_shadow=True, is_running=False)
        moving = {s["id"] for s in doc["agent_sessions"]}
        for s in doc["agent_sessions"]:
            s.update(tenant_id=self.tenant, project_id=self.project)
            # The chat or triage session that started an investigation stays behind.
            parent = s.get("parent_session_id")
            if parent and parent not in moving:
                s["agent_metadata"] = {
                    **(s.get("agent_metadata") or {}),
                    "pov_parent_session_id": parent,
                }
                s["parent_session_id"] = None
                self.detached_parents += 1
            if s.get("status") in LIVE_SESSION_STATUSES:
                s.update(status="stopped", queued_msgs=[])
        for f in doc["feedbacks"]:
            f.update(tenant_id=self.tenant, project_id=self.project)
        return doc


async def target_columns(conn) -> dict[str, dict[str, dict]]:
    rows = await conn.fetch(
        """select table_name, column_name, is_nullable, column_default
           from information_schema.columns where table_schema = 'public' and table_name = any($1)""",
        TABLES,
    )
    cols = defaultdict(dict)
    for r in rows:
        cols[r["table_name"]][r["column_name"]] = {
            "nullable": r["is_nullable"] == "YES",
            "default": r["column_default"],
        }
    return cols


def plan_columns(manifest: dict, target: dict) -> tuple[dict[str, list[str]], list[str]]:
    """Columns to insert per table, plus the problems that must stop the run."""
    problems, insert_cols = [], {}
    set_by_import = {"tenant_id", "project_id"}
    for t in TABLES:
        if t not in target:
            problems.append(f"{t}: missing on the target")
            continue
        src = set(manifest["columns"][t])
        for col, info in target[t].items():
            if (
                col not in src
                and col not in set_by_import
                and not info["nullable"]
                and info["default"] is None
            ):
                problems.append(f"{t}.{col}: required on the target, absent in the bundle")
        dropped = src - set(target[t])
        if dropped:
            print(f"  note: {t} drops source-only columns {sorted(dropped)}")
        insert_cols[t] = [c for c in target[t] if c in src or c in set_by_import]
    return insert_cols, problems


async def insert_rows(conn, table: str, cols: list[str], rows: list[dict]):
    if not rows:
        return
    col_sql = ", ".join(f'"{c}"' for c in cols)
    await conn.execute(
        f"insert into {table} ({col_sql}) select {col_sql} from jsonb_populate_recordset(null::{table}, $1::jsonb)",
        json.dumps(rows),
    )


async def import_one(conn, doc: dict, cols: dict[str, list[str]]):
    msgs = doc["agent_session_messages"]
    new_ids = (
        [
            r[0]
            for r in await conn.fetch(
                "select nextval('agent_session_messages_id_seq') from generate_series(1, $1)",
                len(msgs),
            )
        ]
        if msgs
        else []
    )
    id_map = {}
    for m, new in zip(msgs, new_ids, strict=True):
        id_map[m["id"]] = new
        m["id"] = new
    calls = doc["tool_calls"]
    for c in calls:
        c.pop("id", None)
        if c.get("message_id") is not None:
            if c["message_id"] not in id_map:
                raise ValueError(
                    f"tool call {c.get('tool_call_id')} points at message {c['message_id']} outside the bundle"
                )
            c["message_id"] = id_map[c["message_id"]]

    sessions = sorted(doc["agent_sessions"], key=lambda s: s.get("parent_session_id") is not None)
    async with conn.transaction():
        await insert_rows(conn, "investigations", cols["investigations"], doc["investigations"])
        await insert_rows(conn, "hypotheses", cols["hypotheses"], doc["hypotheses"])
        await insert_rows(conn, "agent_sessions", cols["agent_sessions"], sessions)
        await insert_rows(conn, "agent_session_messages", cols["agent_session_messages"], msgs)
        await insert_rows(conn, "tool_calls", [c for c in cols["tool_calls"] if c != "id"], calls)
        await insert_rows(conn, "feedbacks", cols["feedbacks"], doc["feedbacks"])


def investigation_exists(inv_id: str):
    async def check(conn) -> bool:
        return bool(await conn.fetchval("select 1 from investigations where id = $1::uuid", inv_id))

    return check


async def import_(args):
    bundle = Path(args.bundle)
    manifest = json.loads((bundle / "manifest.json").read_text())
    session = Session(args.db, CLAIM)
    conn = await session.open()
    report = {
        "started_at": datetime.now(UTC).isoformat(),
        "imported": [],
        "skipped_existing": [],
        "failed": {},
    }
    started = time.monotonic()
    try:
        print(
            f"target revision {await revision(conn)}; bundle from {manifest['source_revision']}, {len(manifest['investigation_ids'])} investigations"
        )
        cols, problems = plan_columns(manifest, await target_columns(conn))

        ids = manifest["investigation_ids"]
        existing = {
            str(r["id"]): r
            for r in await conn.fetch(
                "select id, tenant_id, project_id, is_shadow from investigations where id = any($1::uuid[])",
                ids,
            )
        }
        clash = [
            i
            for i, r in existing.items()
            if not (
                r["tenant_id"] == args.tenant and r["project_id"] == args.project and r["is_shadow"]
            )
        ]
        if clash:
            problems.append(
                f"{len(clash)} investigation ids already exist on the target and are not ours, e.g. {clash[:3]}"
            )
        foreign_sessions = await conn.fetch(
            "select id from agent_sessions where id = any($1::text[]) and (tenant_id <> $2 or coalesce(project_id, '') <> $3)",
            manifest["session_ids"],
            args.tenant,
            args.project,
        )
        if foreign_sessions:
            problems.append(
                f"{len(foreign_sessions)} session ids already exist on the target and are not ours, e.g. {[r['id'] for r in foreign_sessions[:3]]}"
            )
        if manifest["orphan_sessions"]:
            print(
                f"  note: {len(manifest['orphan_sessions'])} source sessions point at a missing parent; they are not in any tree"
            )
        if problems:
            print("STOPPED before writing anything:")
            for p in problems:
                print(f"  - {p}")
            sys.exit(2)

        todo = [i for i in ids if i not in existing]
        report["skipped_existing"] = [i for i in ids if i in existing]
        print(
            f"  {len(report['skipped_existing'])} already imported (skipped), {len(todo)} to import"
        )
        check_ram_headroom(bundle, todo)
        if args.dry_run:
            print("dry run: checks passed, nothing written")
            return

        transform = Transform(args.tenant, args.project)
        for n, inv_id in enumerate(todo, 1):
            t0, written = time.monotonic(), {}

            async def write(conn, inv_id=inv_id, written=written):
                # Fresh from the file on every try: import_one renumbers ids in place.
                doc = transform.apply(
                    json.loads((bundle / "investigations" / f"{inv_id}.json").read_text())
                )
                await import_one(conn, doc, cols)
                written["messages"] = len(doc["agent_session_messages"])

            try:
                why = await session.write_item(inv_id, write, exists=investigation_exists(inv_id))
            except RunStopped as e:
                raise RunStopped(f"{e} after {len(report['imported'])} imported") from e
            if why:
                report["failed"][inv_id] = why
                print(f"  FAILED {inv_id}: {why}")
            else:
                report["imported"].append(
                    {"id": inv_id, "seconds": round(time.monotonic() - t0, 3), **written}
                )
            if n % 25 == 0 or n == len(todo):
                done = time.monotonic() - started
                eta = done / n * (len(todo) - n)
                print(
                    f"  {n}/{len(todo)} done, {len(report['failed'])} failed, {done:.0f}s elapsed, ~{eta:.0f}s left"
                )
        report["detached_parent_links"] = transform.detached_parents
    except Exception as e:
        if not (isinstance(e, RunStopped) or outside_problem(e)):
            raise
        report["stopped"] = str(e)
        print(
            f"STOPPED: {type(e).__name__}: {e}. Nothing is half-written; rerun the same command to continue."
        )
        sys.exit(3)
    finally:
        await session.close()
        report["seconds"] = round(time.monotonic() - started, 1)
        if args.report:
            Path(args.report).write_text(json.dumps(report, indent=1))

    print(
        f"imported {len(report['imported'])}, failed {len(report['failed'])}, skipped {len(report['skipped_existing'])} in {report['seconds']}s"
    )
    if report.get("detached_parent_links"):
        print(
            f"  {report['detached_parent_links']} transcripts started by a chat or triage session: link kept as pov_parent_session_id"
        )
    if report["failed"]:
        sys.exit(1)


# ---------------------------------------------------------------- verify / undo


async def verify(args):
    manifest = json.loads((Path(args.bundle) / "manifest.json").read_text())
    ids, sids = manifest["investigation_ids"], manifest["session_ids"]
    conn = await connect(args.db)
    try:
        got = {
            "investigations": await conn.fetchval(
                "select count(*) from investigations where id = any($1::uuid[]) and tenant_id = $2",
                ids,
                args.tenant,
            ),
            "hypotheses": await conn.fetchval(
                "select count(*) from hypotheses where investigation_id = any($1::uuid[])", ids
            ),
            "agent_sessions": await conn.fetchval(
                "select count(*) from agent_sessions where id = any($1::text[]) and tenant_id = $2",
                sids,
                args.tenant,
            ),
            "agent_session_messages": await conn.fetchval(
                "select count(*) from agent_session_messages where session_id = any($1::text[])",
                sids,
            ),
            "tool_calls": await conn.fetchval(
                "select count(*) from tool_calls where session_id = any($1::text[])", sids
            ),
            "feedbacks": await conn.fetchval(
                "select count(*) from feedbacks where target_type = 'investigation' and target_id = any($1::uuid[]) and tenant_id = $2",
                ids,
                args.tenant,
            ),
        }
        visible = await conn.fetchval(
            "select count(*) from investigations where id = any($1::uuid[]) and (not is_shadow or is_running)",
            ids,
        )
        wrong_project = await conn.fetchval(
            "select count(*) from investigations where id = any($1::uuid[]) and project_id is distinct from $2",
            ids,
            args.project,
        )
    finally:
        await conn.close()
    ok = True
    for t, n in got.items():
        want = manifest["counts"].get(t, 0)
        flag = "ok" if n == want else "MISMATCH"
        ok &= n == want
        print(f"  {t:24} target {n:>7}  bundle {want:>7}  {flag}")
    print(f"  visible or running: {visible} (want 0); wrong project: {wrong_project} (want 0)")
    ok &= visible == 0 and wrong_project == 0
    print("VERIFIED" if ok else "NOT VERIFIED")
    if not ok:
        sys.exit(1)


UNDO_BATCH = 50  # ids per transaction: short locks on a live database

# Children before parents: tool_calls.message_id has no index, so a cascading message delete
# scans all of tool_calls per message (10+ min at 4x); deleting our tool calls first avoids that.
OURS = "s.id = any($1::text[]) and s.tenant_id = $2 and s.project_id = $3"
UNDO_STEPS = [
    (
        "tool calls",
        "sessions",
        f"from tool_calls t using agent_sessions s where t.session_id = s.id and {OURS}",
    ),
    (
        "messages",
        "sessions",
        f"from agent_session_messages m using agent_sessions s where m.session_id = s.id and {OURS}",
    ),
    ("transcripts", "sessions", f"from agent_sessions s where {OURS}"),
    (
        "feedbacks",
        "investigations",
        "from feedbacks where target_id = any($1::uuid[]) and tenant_id = $2 and project_id = $3",
    ),
    (
        "investigations",
        "investigations",
        "from investigations where id = any($1::uuid[]) and tenant_id = $2 and project_id = $3 and is_shadow",
    ),
]


def _count_sql(frm: str) -> str:
    # "from a x using b y where ..." counts as "from a x join b y on true where ..."
    return (
        "select count(*) "
        + frm.replace(" using ", " join ", 1).replace(" where ", " on true where ", 1)
        if " using " in frm
        else "select count(*) " + frm
    )


async def undo(args):
    """Delete what the bundle names, in small batches. Safe to stop and rerun at any point."""
    manifest = json.loads((Path(args.bundle) / "manifest.json").read_text())
    ids = {"sessions": manifest["session_ids"], "investigations": manifest["investigation_ids"]}
    session = Session(args.db, CLAIM)
    conn = await session.open()
    started = time.monotonic()
    try:
        for label, kind, frm in UNDO_STEPS:
            if args.dry_run:
                n = await conn.fetchval(_count_sql(frm), ids[kind], args.tenant, args.project)
                print(f"  would delete {n} {label}")
                continue
            t0, total = time.monotonic(), 0
            for i in range(0, len(ids[kind]), UNDO_BATCH):
                async with conn.transaction():
                    status = await conn.execute(
                        "delete " + frm, ids[kind][i : i + UNDO_BATCH], args.tenant, args.project
                    )
                total += int(status.split()[-1])
            print(f"  deleted {total} {label} in {time.monotonic() - t0:.1f}s")
            if label == "tool calls" and total:
                # Shrink the table so each message delete's check has nothing to scan.
                try:
                    await conn.execute("vacuum tool_calls")
                    print("  vacuumed tool_calls")
                except Exception as e:  # not the table owner, most likely
                    print(
                        f"  could not vacuum tool_calls ({type(e).__name__}); message deletes will be slow"
                    )
    except Exception as e:  # each batch is all-or-nothing
        if not outside_problem(e):
            raise
        print(
            f"STOPPED: undo interrupted: {type(e).__name__}: {e}\nevery finished batch is deleted and the current one rolled back; rerun undo to finish"
        )
        sys.exit(3)
    finally:
        await session.close()
    print(
        "dry run, nothing deleted"
        if args.dry_run
        else f"undo finished in {time.monotonic() - started:.1f}s (hypotheses and derived rows went with their investigation)"
    )


def add_commands(sub):
    e = sub.add_parser("export-investigations", help="old agents DB -> bundle")
    e.add_argument("--db", help="postgresql://... of the old agents DB (else POSTGRES_CONFIG__*)")
    e.add_argument("--out", required=True, help="a fresh bundle folder")
    e.add_argument(
        "--select",
        default="all",
        help="'all' (default), 'sample' (one investigation per shape worth testing), or comma-separated ids",
    )

    for name in ("import-investigations", "verify-investigations", "undo-investigations"):
        s = sub.add_parser(name)
        s.add_argument("--bundle", required=True)
        s.add_argument(
            "--db", help="postgresql://... of the new agents DB (else POSTGRES_CONFIG__*)"
        )
        s.add_argument("--tenant", required=True, help="tenant id on the new install")
        s.add_argument("--project", required=True, help="project id on the new install")
        if name != "verify-investigations":
            s.add_argument("--dry-run", action="store_true")
    imp = sub.choices["import-investigations"]
    imp.add_argument("--report", help="write a JSON report of the run here")


COMMANDS = {
    "export-investigations": export,
    "import-investigations": import_,
    "verify-investigations": verify,
    "undo-investigations": undo,
}
