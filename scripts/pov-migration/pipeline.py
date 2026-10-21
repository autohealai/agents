"""migrate-all: the whole migration as one command.

It checks access, exports from the old database, rewrites the memories, dry-runs every import
(nothing is written unless all pass), then moves skills, memories, labels and investigations,
each followed by its verify. Every step skips what is already done, so after any stop you
rerun the same command.
"""

import argparse
import inspect
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import investigations
import labels
import memories
import skills
from api import api_args
from db import outside_problem

PARTS = ("skills", "memories", "labels", "investigations")


async def step(name: str, fn, args: SimpleNamespace, results: list):
    """Run one command; stop the whole run unless it succeeds."""
    print(f"\n=== {name}")
    t0, code = time.monotonic(), 0
    try:
        out = fn(args)
        if inspect.isawaitable(out):
            await out
    except SystemExit as e:
        if isinstance(e.code, str):
            print(e.code)
        code = e.code if isinstance(e.code, int) else (1 if e.code else 0)
    except Exception as e:  # e.g. the database is down when the step starts
        if not outside_problem(e):
            raise
        print(f"STOPPED: {type(e).__name__}: {e}")
        code = 3
    results.append((name, code, round(time.monotonic() - t0, 1)))
    if code:
        stop(
            results,
            f"STOPPED at '{name}' (exit {code}). Fix what it says, then rerun this same command.",
            code,
        )


def stop(results: list, message: str, code: int):
    print("\n=== summary")
    for name, c, secs in results:
        print(f"  {'ok    ' if c == 0 else f'exit {c}'}  {name:34} {secs:>7}s")
    print(message)
    sys.exit(code)


async def migrate_all(a):
    bundle = Path(a.bundle)
    bundle.mkdir(parents=True, exist_ok=True)
    skip = set(filter(None, (a.skip or "").split(",")))
    if unknown := skip - set(PARTS):
        sys.exit(f"--skip takes {', '.join(PARTS)}; not {sorted(unknown)}")
    if "memories" in skip:
        skip.add("labels")  # labels need the memories
    run = {p: p not in skip for p in PARTS}
    needs_api = run["skills"] or run["labels"]
    if needs_api and not a.domain:
        sys.exit("--domain and a token are needed for skills and labels (or --skip skills,labels)")
    db = dict(db=a.db, tenant=a.tenant, project=a.project)
    api = dict(domain=a.domain, token_file=a.token_file, project=a.project)
    results: list = []

    if needs_api:
        await step(
            "check access (probe)", skills.COMMANDS["probe"], SimpleNamespace(**api), results
        )

    # Exports: each writes its "done" marker last, so a cut-off export is redone, a finished one skipped.
    exports = [
        (
            "skills",
            bundle / "skills",
            "export-skills",
            SimpleNamespace(source_db=a.source_db, out=str(bundle)),
        ),
        (
            "memories",
            bundle / "memories_manifest.json",
            "export-memories",
            SimpleNamespace(db=a.source_db, out=str(bundle)),
        ),
        (
            "investigations",
            bundle / "manifest.json",
            "export-investigations",
            SimpleNamespace(db=a.source_db, out=str(bundle), select="all"),
        ),
    ]
    for part, done, name, args in exports:
        if not run[part] or done.exists():
            continue
        if not a.source_db:
            sys.exit(
                f"{name} has not run yet: pass --source-db (the old install's agents database)"
            )
        fn = {
            "export-skills": skills.COMMANDS["export-skills"],
            "export-memories": memories.COMMANDS["export-memories"],
            "export-investigations": investigations.COMMANDS["export-investigations"],
        }[name]
        await step(name, fn, args, results)

    if run["memories"]:
        convert = SimpleNamespace(
            bundle=str(bundle),
            agents_py=a.agents_py,
            only=None,
            model=a.model,
            fake=a.fake,
            concurrency=a.concurrency,
            attempts=3,
            retries=3,
            force=False,
        )
        await step("convert-memories", memories.COMMANDS["convert-memories"], convert, results)

    # Every check before any write.
    if run["skills"]:
        await step(
            "push-skills (dry run)",
            skills.COMMANDS["push-skills"],
            SimpleNamespace(**api, dir=str(bundle), branch=None, dry_run=True),
            results,
        )
    if run["memories"]:
        await step(
            "import-memories (dry run)",
            memories.COMMANDS["import-memories"],
            SimpleNamespace(**db, bundle=str(bundle), dry_run=True, report=None),
            results,
        )
    if run["labels"]:
        await step(
            "label-memories (dry run)",
            labels.COMMANDS["label-memories"],
            SimpleNamespace(
                **api,
                bundle=str(bundle),
                label_map=a.label_map,
                concurrency=8,
                dry_run=True,
                show=0,
            ),
            results,
        )
    if run["investigations"]:
        await step(
            "import-investigations (dry run)",
            investigations.COMMANDS["import-investigations"],
            SimpleNamespace(**db, bundle=str(bundle), dry_run=True, report=None),
            results,
        )

    reports = bundle / "reports"
    reports.mkdir(exist_ok=True)
    if run["skills"]:
        await step(
            "push-skills",
            skills.COMMANDS["push-skills"],
            SimpleNamespace(**api, dir=str(bundle), branch=None, dry_run=False),
            results,
        )
    if run["memories"]:
        await step(
            "import-memories",
            memories.COMMANDS["import-memories"],
            SimpleNamespace(
                **db,
                bundle=str(bundle),
                dry_run=False,
                report=str(reports / "memories.json"),
            ),
            results,
        )
        await step(
            "verify-memories",
            memories.COMMANDS["verify-memories"],
            SimpleNamespace(**db, bundle=str(bundle)),
            results,
        )
    if run["labels"]:
        lab = dict(api, bundle=str(bundle), label_map=a.label_map, concurrency=8)
        await step(
            "label-memories",
            labels.COMMANDS["label-memories"],
            SimpleNamespace(**lab, dry_run=False, show=0),
            results,
        )
        await step(
            "verify-labels", labels.COMMANDS["verify-labels"], SimpleNamespace(**lab), results
        )
    if run["investigations"]:
        await step(
            "import-investigations",
            investigations.COMMANDS["import-investigations"],
            SimpleNamespace(
                **db,
                bundle=str(bundle),
                dry_run=False,
                report=str(reports / "investigations.json"),
            ),
            results,
        )
        await step(
            "verify-investigations",
            investigations.COMMANDS["verify-investigations"],
            SimpleNamespace(**db, bundle=str(bundle)),
            results,
        )
    stop(
        results,
        "\nDONE. Check the Skills page, the Memories page and an investigation link in the app.",
        0,
    )


def add_commands(sub):
    m = sub.add_parser("migrate-all", help="the whole migration, in order, in one run")
    m.add_argument("--bundle", required=True, help="working folder; reruns pick up from it")
    m.add_argument(
        "--source-db", help="the old install's agents database (needed until the exports have run)"
    )
    m.add_argument("--db", help="the new install's agents database (else POSTGRES_CONFIG__*)")
    m.add_argument("--tenant", required=True)
    m.add_argument("--project", required=True)
    api_args(m, required=False)
    m.add_argument("--label-map", help="customer label map JSON (see label-maps/)")
    m.add_argument(
        "--model",
        help="model for the memory conversion (else AGENT_CONFIG__MODEL_PROVIDER_DEFAULT)",
    )
    m.add_argument(
        "--agents-py", help="agents-py root to import from (else AGENTS_PY_ROOT or /app)"
    )
    m.add_argument("--concurrency", type=int, default=8, help="memories converted at once")
    m.add_argument("--skip", help=f"comma-separated parts to leave out: {', '.join(PARTS)}")
    # A stand-in model, for rehearsing the pipeline without an LLM; hidden from --help.
    m.add_argument(
        "--fake", choices=["ok", "flaky", "slow", "ratelimit", "leaky"], help=argparse.SUPPRESS
    )


COMMANDS = {"migrate-all": migrate_all}
