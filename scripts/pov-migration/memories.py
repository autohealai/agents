"""Convert old POV memories into the new memory store.

export-memories   old agents DB -> memories_source.jsonl + agents_md.md in the bundle
convert-memories  LLM rewrites each memory as Use when / What to do / Avoid when,
                  validated by the app's own MemoryDraft. Writes memories_converted.jsonl
                  for review. Touches no database. Rerun converts only what is missing.
                  A draft that adds names, ids, dates or numbers the lesson never mentions
                  gets another try; if it keeps adding them, it is held for review.
accept-memories   keep a held draft as written, after a person read it
import-memories   converted memories -> new agents DB, one transaction per memory
verify-memories / undo-memories

convert-memories imports agents-py (model factory, MemoryDraft), so run it where
agents-py is importable: inside an agents-py pod, or with --agents-py pointing at a checkout.
"""

import asyncio
import hashlib
import json
import os
import re
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from db import (
    RunStopped,
    Session,
    columns_of,
    connect,
    load_user_map,
    outside_problem,
    read_jsonl,
    require_columns,
    revision,
)

MOVING = {"applied": "active", "consolidated_into_skill": "active", "pending": "pending"}
ALWAYS_READ = [
    "architecture-overview",
    "investigation-steps",
    "investigation-environments",
    "investigation-proactive-actions",
]
PROFILE_ID = "default_profile"  # agents-py's DEFAULT_PROFILE_ID; Git runs search memories under it
ID_NS = uuid.UUID("6f1d3c52-6d1a-4b52-9a83-3b5d1b4e7c11")
AUTHOR = "pov-migration"
# Import and undo share one claim, so they never run at the same time.
CLAIM = "pov-migration:memories"
SOURCE_COLUMNS = {
    "ekb_tactical_memories": [
        "id",
        "status",
        "title",
        "content",
        "source_metadata",
        "source_investigation_id",
        "source_hypothesis_id",
        "accept_type",
        "resolved_at",
        "resolved_by_user_id",
        "created_at",
    ],
    "hypotheses": [
        "id",
        "investigation_id",
        "name",
        "description",
        "confidence",
        "status",
        "is_primary",
        "causal_chain",
        "mitigating_fixes",
    ],
    "agentsmd_latest_sections": ["section_id"],
    "agentsmd_sections": ["id", "name", "title", "content"],
}
TARGET_COLUMNS = {
    "agent_memories": [
        "id",
        "tenant_id",
        "profile_id",
        "status",
        "owner_user_id",
        "provenance",
        "project_id",
        "created_at",
        "current_revision_id",
        "index_enqueued_at",
    ],
    "agent_memory_revisions": [
        "id",
        "memory_id",
        "title",
        "content",
        "applies_when",
        "guidance",
        "avoid_when",
        "author",
    ],
    "agent_memory_proposals": [
        "id",
        "tenant_id",
        "profile_id",
        "kind",
        "status",
        "proposed_memory_id",
        "reasoning",
        "producer_key",
        "reviewed_by_user_id",
        "reviewed_at",
        "project_id",
        "created_at",
    ],
}


def ids_for(legacy_id: str) -> dict[str, str]:
    """Fixed ids, so a rerun finds its own rows and undo knows what to delete."""
    return {
        k: str(uuid.uuid5(ID_NS, f"{legacy_id}:{k}")) for k in ("memory", "revision", "proposal")
    }


# ---------------------------------------------------------------- export


async def export_memories(args):
    out = Path(args.out)
    if (out / "memories_manifest.json").exists():  # written last, so only a finished export has it
        sys.exit(f"{out} already holds a memory export; use a fresh folder")
    out.mkdir(parents=True, exist_ok=True)
    conn = await connect(args.db)
    try:
        await require_columns(conn, SOURCE_COLUMNS)
        # Older installs keep every section tenant-wide and have no profile_id column.
        tenant_wide = (
            "l.profile_id is null and"
            if "profile_id" in await columns_of(conn, "agentsmd_latest_sections")
            else ""
        )
        sections = await conn.fetch(
            f"""select s.name, s.title, s.content from agentsmd_latest_sections l
                join agentsmd_sections s on s.id = l.section_id
                where {tenant_wide} s.name = any($1) and coalesce(s.content, '') <> ''""",
            ALWAYS_READ,
        )
        by_name = {r["name"]: r for r in sections}
        agents_md = "\n\n".join(
            f"## {by_name[n]['title']}\n\n{by_name[n]['content'].strip()}"
            for n in ALWAYS_READ
            if n in by_name
        )
        (out / "agents_md.md").write_text(agents_md)

        rows = await conn.fetch(
            """select row_to_json(m)::text j from ekb_tactical_memories m
               where status = any($1) order by created_at""",
            list(MOVING),
        )
        skipped = await conn.fetch(
            "select status, count(*) n from ekb_tactical_memories where not (status = any($1)) group by 1",
            list(MOVING),
        )
        n_mismatch = 0
        with open(out / "memories_source.jsonl", "w") as f:
            for r in rows:
                m = json.loads(r["j"])
                hyps = await conn.fetch(
                    """select id::text, name, description, confidence, status, is_primary, causal_chain, mitigating_fixes
                       from hypotheses where investigation_id::text = $1
                       order by confidence desc nulls last, is_primary desc""",
                    m["source_investigation_id"] or "",
                )
                chosen = hyps[0] if hyps else None  # the highest-confidence hypothesis
                if (
                    hyps
                    and m["source_hypothesis_id"]
                    and hyps[0]["id"] != m["source_hypothesis_id"]
                ):
                    n_mismatch += 1
                hyp = None
                if chosen:
                    hyp = {
                        k: chosen[k] for k in ("id", "name", "description", "status", "is_primary")
                    }
                    hyp["confidence"] = (
                        float(chosen["confidence"]) if chosen["confidence"] is not None else None
                    )
                    hyp["causal_chain"] = (
                        json.loads(chosen["causal_chain"])
                        if isinstance(chosen["causal_chain"], str)
                        else chosen["causal_chain"]
                    )
                    hyp["mitigating_fixes"] = (
                        json.loads(chosen["mitigating_fixes"])
                        if isinstance(chosen["mitigating_fixes"], str)
                        else chosen["mitigating_fixes"]
                    )
                f.write(json.dumps({"memory": m, "hypothesis": hyp}) + "\n")
        manifest = {
            "created_at": datetime.now(UTC).isoformat(),
            "source_revision": await revision(conn),
            "hypothesis_rule": "top",
            "moving": len(rows),
            "not_moving": {r["status"]: r["n"] for r in skipped},
            "source_hypothesis_not_top": n_mismatch,
            "agents_md_sections": [n for n in ALWAYS_READ if n in by_name],
            "agents_md_chars": len(agents_md),
        }
        (out / "memories_manifest.json").write_text(json.dumps(manifest, indent=1))
    finally:
        await conn.close()
    print(f"exported {len(rows)} memories; not moving: {manifest['not_moving']}")
    print(f"  agents.md: {manifest['agents_md_sections']} ({len(agents_md)} chars)")
    print(
        f"  {n_mismatch} memories came from a hypothesis that is not the top one (the LLM sees the top one)"
    )


# ---------------------------------------------------------------- convert

INSTRUCTIONS = """\
You restate one lesson that an incident-investigation agent saved on an older version of
Autoheal, so it fits the new memory format. A person already reviewed and accepted this
lesson. Your job is to say the same thing in the new shape, not to judge it or improve it.

## Stay faithful to the lesson

The lesson text is your only source of facts.

- Never add a name, id, ticket number, date, time, number, host, class, query or cause that
  is not in the lesson text. If it is not there, leave it out, even when the background
  below mentions it.
- Keep the lesson as general as it is. A general heuristic must not be narrowed to the one
  incident it came from.
- Keep its emphasis. Do not turn a caution into an instruction, or a "check first" into a
  fix.
- The investigation, its root-cause hypothesis and the team's context are background. Use
  them only to understand what the lesson means, for example what "the alert" or "this
  job" refers to.

## The shape

- `title`: a specific, searchable phrase, at most 60 characters.
- `applies_when`: the recognizable future situation where the lesson helps, at most 120
  characters. Do not start it with "when".
- `guidance`: one complete, direct sentence saying what to do or conclude, at most 240
  characters.
- `avoid_when`: a look-alike situation where the lesson does not apply, and only one the
  lesson text itself names, such as "distinct from X" or "not Y". Write it as a situation
  someone can recognize, not as an action or a warning, and never as the situation the
  lesson is about. At most 160 characters, not starting with "when". If the lesson names
  no such case, leave it unset.

Aim for 180-350 characters across the memory and never exceed 600. Keep the concrete
signal, command, component or error text that makes the lesson useful.

Write as one engineer explaining a reusable lesson to another engineer who did not see the
original work: simple, coherent sentences in ordinary engineering words. Do not compress it
into labels or fragments, and do not write narration such as "the run showed" or "it was
learned", or filler such as "ensure robustness" or "consider the context".

Good wording looks like this. It is a different domain; never copy anything from it:

  title: Query child digests for multi-arch ECR coverage
  applies_when: Inspector reports no coverage for a multi-arch ECR index
  guidance: Resolve the index to its per-architecture child digests and query those because Inspector attaches findings to the child manifests.
  avoid_when: the image is a single-architecture manifest

## The team's context (background only)

Their agents.md, which the investigation agent always read:

{agents_md}
"""


def lesson_text(m: dict) -> str:
    """The memory's own words: title, when it applies (the old trigger) and the lesson."""
    trigger = (m.get("source_metadata") or {}).get("trigger")
    when = f"When it applies: {trigger}\n\n" if isinstance(trigger, str) and trigger.strip() else ""
    return f"Title: {m['title']}\n\n{when}{m['content']}"


def prompt_for(item: dict) -> str:
    m, h = item["memory"], item["hypothesis"]
    md = m.get("source_metadata") or {}
    lesson = f"# The lesson (the only source of facts)\n\n{lesson_text(m)}"
    background = [f"Investigation it came from: {md.get('investigation_title') or 'not recorded'}"]
    if h:
        chain = h.get("causal_chain") or []
        steps = [s.get("step") if isinstance(s, dict) else str(s) for s in chain][:8]
        background.append(
            f"Root-cause hypothesis ({h.get('status')}, confidence {h.get('confidence')}): {h.get('name')}\n"
            f"{h.get('description') or ''}\n" + "\n".join(f"- {s}" for s in steps if s)
        )
    return (
        lesson
        + "\n\n# Background (to understand the lesson, not to add to it)\n\n"
        + "\n\n".join(background)
    )


# Words that look like identifiers but are common enough to appear without being a leak.
COMMON_TOKENS = {
    "api",
    "apis",
    "http",
    "https",
    "url",
    "sql",
    "db",
    "dbs",
    "ui",
    "id",
    "ids",
    "iis",
    "sop",
    "sops",
    "rca",
    "idp",
    "json",
    "dns",
    "tls",
    "ssl",
    "cpu",
    "ram",
    "jwt",
    "sso",
    "oauth",
    "ci",
    "cd",
    "vm",
    "vms",
    "dtu",
    "prod",
    "pr",
    "etl",
    "sla",
    "slo",
    "utc",
    "et",
    "pst",
    "est",
    "ip",
    "tcp",
    "udp",
    "ssh",
    "cli",
    "sdk",
    "aws",
    "gcp",
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "not",
    "and",
    "all",
    "any",
    "only",
    "never",
    "must",
    "e.g",
    "i.e",
}
_DATE_TIME = r"\b\d{1,4}[/-]\d{1,2}(?:[/-]\d{1,4})?\b|\b\d{1,2}:\d{2}\b"  # 04/24, 2026-07-16, 20:45
_CODE = (
    r"[A-Za-z_][\w-]*(?:[./][\w{}-]+)+"  # dotted names and paths: card.amount, v1/vcc/x
    r"|\b(?=[A-Za-z]*\d)(?=\d*[A-Za-z])\w+\b"  # letters and digits: INC0719466, PRHVSL01, Org2
    r"|\b[a-z]+[A-Z]\w*|\b[A-Z][a-z]+[A-Z]\w*"  # camelCase, PascalCase
    r"|\b[A-Z]{3,}\b|\b\w+_\w+\b"  # ALLCAPS, snake_case
)
_NUMBER = r"\b\d+(?:\.\d+)?\b"


def _tokens(text: str) -> set[str]:
    # "empty/timeout" is two words, not a path
    text = " ".join(
        w.replace("/", " ") if re.fullmatch(r"[\W]*[A-Za-z]+(?:/[A-Za-z]+)+[\W]*", w) else w
        for w in text.split()
    )
    found = {t.lower() for t in re.findall(_DATE_TIME, text)}
    rest = re.sub(_DATE_TIME, " ", text)
    for pattern in (_CODE, _NUMBER):
        found |= {t.strip(".-").lower() for t in re.findall(pattern, rest)}
    return {t for t in found if t and t not in COMMON_TOKENS}


def added_identifiers(lesson: str, draft) -> list[str]:
    """Identifier-like words in the draft that the lesson text never mentions."""
    lesson_l = lesson.lower()
    squashed = re.sub(r"\s+", "", lesson_l)  # "App Insights" covers "AppInsights"
    known = _tokens(lesson) | set(
        re.findall(r"\d+(?:\.\d+)?", lesson)
    )  # "500s" and "50-100x" cover 500 and 100
    text = " ".join(
        filter(None, [draft.title, draft.applies_when, draft.guidance, draft.avoid_when])
    )
    new = []
    for t in sorted(_tokens(text)):
        if t in known:
            continue
        if not re.fullmatch(
            r"[\d.:/-]+", t
        ):  # a number must match exactly; a name may sit inside a longer one
            parts = [p for p in re.split(r"[./_{}-]+", t) if p]
            if t in squashed or all(p in squashed for p in parts):
                continue
        new.append(t)
    return new


def input_hash(item: dict, agents_md: str, model: str) -> str:
    raw = json.dumps(
        [INSTRUCTIONS, prompt_for(item), hashlib.sha256(agents_md.encode()).hexdigest(), model],
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


async def convert_memories(args):
    os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
    root = args.agents_py or os.environ.get("AGENTS_PY_ROOT") or "/app"
    sys.path.insert(0, root)
    try:
        from pydantic_ai import Agent, ModelRetry
        from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior, UserError
        from src.modules.self_improvement.domain.generation_dto import MemoryDraft
    except ImportError as e:
        sys.exit(f"cannot import agents-py from {root}: {e}")

    bundle = Path(args.bundle)
    agents_md = (bundle / "agents_md.md").read_text()
    items = read_jsonl(bundle / "memories_source.jsonl")
    if args.only:
        wanted = set(args.only.split(","))
        items = [i for i in items if i["memory"]["id"] in wanted]

    model_name = args.model or os.environ.get("AGENT_CONFIG__MODEL_PROVIDER_DEFAULT")
    if args.fake:
        model, model_name = fake_model(args.fake), f"fake:{args.fake}"
    else:
        if not model_name:
            sys.exit("no --model and no AGENT_CONFIG__MODEL_PROVIDER_DEFAULT")
        from src.platform.model_factory import infer_model_for

        model = infer_model_for(model_name)
    agent = Agent(
        model,
        output_type=MemoryDraft,
        deps_type=dict,
        instructions=INSTRUCTIONS.format(agents_md=agents_md),
        retries=args.retries,
    )

    @agent.output_validator
    def faithful(ctx, draft):
        ctx.deps["rejected"] = None
        if added := added_identifiers(ctx.deps["lesson"], draft):
            ctx.deps["rejected"] = {
                "draft": draft.model_dump(),
                "content": draft.render_content(),
                "added": added,
            }
            raise ModelRetry(
                f"This adds details the lesson never mentions: {', '.join(added)}. "
                "Rewrite it with only what the lesson text says."
            )
        return draft

    out_path = bundle / "memories_converted.jsonl"
    done = {}  # earlier results are always kept; --force only reconverts the selected memories
    if out_path.exists():
        for line in out_path.read_text().splitlines():
            if line.strip():
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue  # a line cut off by a kill
                done[r["legacy_id"]] = r
    todo = [
        i
        for i in items
        if not (
            (prev := done.get(i["memory"]["id"]))
            and (prev.get("draft") or prev.get("rejected"))
            and prev["input_hash"] == input_hash(i, agents_md, model_name)
            and not args.force
        )
    ]
    print(
        f"{len(items)} memories, {len(items) - len(todo)} already converted, {len(todo)} to convert with {model_name}"
    )

    sem = asyncio.Semaphore(args.concurrency)
    started = time.monotonic()

    async def one(item):
        m = item["memory"]
        rec = {
            "legacy_id": m["id"],
            "input_hash": input_hash(item, agents_md, model_name),
            "model": model_name,
        }
        async with sem:
            for attempt in range(1, args.attempts + 1):
                t0 = time.monotonic()
                deps = {"lesson": lesson_text(m), "rejected": None}
                try:
                    result = await agent.run(prompt_for(item), deps=deps)
                    draft = result.output
                    usage = result.usage() if callable(result.usage) else result.usage
                    fixes = sum(
                        getattr(p, "part_kind", "") == "retry-prompt"
                        for msg in result.all_messages()
                        for p in msg.parts
                    )
                    rec.update(
                        draft=draft.model_dump(),
                        content=draft.render_content(),
                        attempts=attempt,
                        model_retries=fixes,
                        seconds=round(time.monotonic() - t0, 2),
                        input_tokens=usage.input_tokens,
                        output_tokens=usage.output_tokens,
                        cache_read_tokens=getattr(usage, "cache_read_tokens", 0),
                    )
                    rec.pop("error", None)
                    break
                except (TypeError, AttributeError, NameError, KeyError, UserError):
                    raise  # a bug or a model set-up error: stop, it would fail for every memory
                except (
                    UnexpectedModelBehavior
                ) as e:  # broke MemoryDraft's rules, or kept adding details, on every retry
                    if rejected := deps["rejected"]:
                        rec.update(
                            error=f"adds details the lesson never mentions: {', '.join(rejected['added'])}",
                            rejected=rejected,
                            attempts=attempt,
                        )
                    else:
                        cause = e.__cause__ or e.__context__
                        rec.update(error=f"invalid output: {cause or e}"[:600], attempts=attempt)
                    break
                except (
                    Exception
                ) as e:  # rate limits, server errors and timeouts: worth another attempt
                    rec.update(error=f"{type(e).__name__}: {e}"[:400], attempts=attempt)
                    refused = (
                        isinstance(e, ModelHTTPError)
                        and e.status_code < 500
                        and e.status_code != 429
                    )
                    if refused:
                        break  # the model rejects this request every time
                    if attempt < args.attempts:
                        await asyncio.sleep(min(60, 5 * 2 ** (attempt - 1)))
        return rec

    async def one_saved(item):
        rec = await one(item)
        with open(out_path, "a") as f:  # one line per result: a kill loses only what was in flight
            f.write(json.dumps(rec) + "\n")
        return rec

    results = await asyncio.gather(*(one_saved(i) for i in todo))
    for r in results:
        done[r["legacy_id"]] = r
    tmp = out_path.with_suffix(".tmp")
    with open(tmp, "w") as f:  # rewrite once at the end, one line per memory
        for r in done.values():
            f.write(json.dumps(r) + "\n")
    tmp.replace(out_path)

    ok = [r for r in results if r.get("draft")]
    failed = [r for r in results if not r.get("draft")]
    tin = sum(r.get("input_tokens") or 0 for r in ok)
    tout = sum(r.get("output_tokens") or 0 for r in ok)
    retried = sum(1 for r in results if (r.get("attempts") or 1) > 1)
    fixed = sum(1 for r in ok if r.get("model_retries"))
    print(
        f"converted {len(ok)}, needs review {len(failed)} in {time.monotonic() - started:.1f}s; "
        f"tokens in {tin}, out {tout}; {fixed} fixed their draft when told, {retried} needed another attempt"
    )
    for r in failed:
        print(f"  needs review {r['legacy_id']}: {r['error']}")
    waiting = [
        i["memory"]["id"]
        for i in read_jsonl(bundle / "memories_source.jsonl")
        if not done.get(i["memory"]["id"], {}).get("draft")
    ]
    if waiting:
        print(
            f"{len(waiting)} memories in this bundle still need review or conversion; only converted ones are imported"
        )
        sys.exit(1)


async def accept_memories(args):
    """A reviewer read a held draft (one that added details) and keeps it as written."""
    path = Path(args.bundle) / "memories_converted.jsonl"
    rows = read_jsonl(path)
    picked = []
    for prefix in args.ids.split(","):
        hits = [r for r in rows if r["legacy_id"].startswith(prefix.strip())]
        if len(hits) != 1:
            sys.exit(f"{prefix}: matches {len(hits)} memories")
        if not hits[0].get("rejected"):
            sys.exit(f"{prefix}: has no held draft to accept")
        picked.append(hits[0])
    for r in picked:
        held = r.pop("rejected")
        r.pop("error", None)
        r.update(draft=held["draft"], content=held["content"], accepted_with_added=held["added"])
        print(f"  accepted {r['legacy_id']}: {held['draft']['title']}")
    tmp = path.with_suffix(".tmp")
    tmp.write_text("".join(json.dumps(r) + "\n" for r in rows))
    tmp.replace(path)


def fake_model(mode: str):
    """A stand-in model for pipeline tests: 'ok' succeeds, 'flaky' breaks the rules for some,
    'slow' takes 0.2 s a call, 'ratelimit' answers 429 to a third of memories on their first try,
    'leaky' adds a ticket number the lesson never mentions.
    """
    import time as _time

    from pydantic_ai.exceptions import ModelHTTPError
    from pydantic_ai.messages import ModelResponse, ToolCallPart
    from pydantic_ai.models.function import FunctionModel

    seen: set[str] = set()

    def respond(messages, info):
        if mode == "slow":
            _time.sleep(0.2)
        prompt = next(
            (
                str(p.content)
                for m in messages
                for p in m.parts
                if getattr(p, "part_kind", "") == "user-prompt"
            ),
            "",
        )
        title = next(
            (
                line.removeprefix("Title: ")
                for line in prompt.splitlines()
                if line.startswith("Title: ")
            ),
            "Lesson",
        )[:60]
        args = {
            "title": title,
            "applies_when": "the same symptom shows up again",
            "guidance": "Follow the lesson's steps before anything else.",
        }
        bucket = int(hashlib.sha256(prompt.encode()).hexdigest(), 16)
        retried = any(
            getattr(p, "part_kind", "") == "retry-prompt" for m in messages for p in m.parts
        )
        if mode == "leaky" and (
            bucket % 2 == 0 or not retried
        ):  # half fix it when told, half never do
            args["guidance"] = "Check INC0000001 first, then follow the lesson's steps."
        if mode == "ratelimit" and bucket % 3 == 0 and prompt not in seen:
            seen.add(prompt)
            raise ModelHTTPError(status_code=429, model_name="fake", body="rate limited")
        if mode == "flaky" and bucket % 4 == 0:
            args["applies_when"] = "when " + "x" * 200  # breaks two MemoryDraft rules
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, args)])

    return FunctionModel(respond)


# ---------------------------------------------------------------- import


async def import_memories(args):
    bundle = Path(args.bundle)
    sources = {i["memory"]["id"]: i for i in read_jsonl(bundle / "memories_source.jsonl")}
    ready = [c for c in read_jsonl(bundle / "memories_converted.jsonl") if c.get("draft")]
    not_ready = sorted(set(sources) - {c["legacy_id"] for c in ready})
    user_map = load_user_map(args.user_map)
    session = Session(args.db, CLAIM)
    conn = await session.open()
    report = {"imported": [], "skipped_existing": [], "failed": {}, "not_converted": not_ready}
    started = time.monotonic()
    try:
        await require_columns(conn, TARGET_COLUMNS, "target")
        ids = {c["legacy_id"]: ids_for(c["legacy_id"]) for c in ready}
        mem_ids = [v["memory"] for v in ids.values()]
        existing = {
            str(r["id"]): r
            for r in await conn.fetch(
                "select id, tenant_id, project_id from agent_memories where id = any($1::uuid[])",
                mem_ids,
            )
        }
        clash = [
            i
            for i, r in existing.items()
            if (r["tenant_id"], r["project_id"]) != (args.tenant, args.project)
        ]
        keys = [f"{AUTHOR}:{c['legacy_id']}" for c in ready]
        key_clash = await conn.fetchval(
            """select count(*) from agent_memory_proposals where tenant_id = $1 and producer_key = any($2)
               and not (proposed_memory_id = any($3::uuid[]))""",
            args.tenant,
            keys,
            mem_ids,
        )
        print(
            f"target revision {await revision(conn)}; {len(ready)} converted, {len(not_ready)} not converted (not imported)"
        )
        if clash or key_clash:
            print("STOPPED before writing anything:")
            if clash:
                print(f"  - {len(clash)} memory ids exist and are not ours")
            if key_clash:
                print(f"  - {key_clash} producer keys exist on proposals that are not ours")
            sys.exit(2)
        todo = [c for c in ready if ids[c["legacy_id"]]["memory"] not in existing]
        report["skipped_existing"] = [
            c["legacy_id"] for c in ready if ids[c["legacy_id"]]["memory"] in existing
        ]
        print(
            f"  {len(report['skipped_existing'])} already imported (skipped), {len(todo)} to import"
        )
        if args.dry_run:
            print("dry run: checks passed, nothing written")
            return

        for n, c in enumerate(todo, 1):
            lid, src = c["legacy_id"], sources[c["legacy_id"]]["memory"]

            async def write(conn, c=c, src=src, lid=lid):
                await import_one(conn, c, src, ids[lid], args.tenant, args.project, user_map)

            try:
                why = await session.write_item(lid, write, exists=memory_exists(ids[lid]["memory"]))
            except RunStopped as e:
                raise RunStopped(f"{e} after {len(report['imported'])} imported") from e
            if why:
                report["failed"][lid] = why
                print(f"  FAILED {lid}: {why}")
            else:
                report["imported"].append(lid)
            if n % 100 == 0 or n == len(todo):
                print(f"  {n}/{len(todo)} done, {len(report['failed'])} failed")
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
    if report["failed"]:
        sys.exit(1)


async def import_one(
    conn, c: dict, src: dict, ids: dict, tenant: str, project: str, user_map: dict
):
    status = MOVING[src["status"]]
    active = status == "active"
    reviewer = (
        user_map.get(src.get("resolved_by_user_id"), src.get("resolved_by_user_id"))
        if active
        else None
    )
    draft = c["draft"]
    md = src.get("source_metadata") or {}
    point = md.get("inflection_point")
    reasoning = None
    if isinstance(point, dict) and all(
        point.get(k) for k in ("what_happened", "before_state", "after_state")
    ):
        reasoning = {
            k: point.get(k)
            for k in ("turn", "trigger_type", "what_happened", "before_state", "after_state")
        }
    extraction = md.get("extraction") if isinstance(md.get("extraction"), dict) else {}
    provenance = {
        "memory_type": extraction.get("information_type"),
        "generalizability": extraction.get("generalizability"),
        "auto_accept_type": src.get("accept_type"),
        "accepted_at": src.get("resolved_at") if active else None,
        "producer": AUTHOR,
    }
    provenance = {k: v for k, v in provenance.items() if v not in (None, "")}

    async with conn.transaction():
        await conn.execute(
            """insert into agent_memories (id, tenant_id, profile_id, status, owner_user_id, provenance, project_id, created_at)
               values ($1, $2, $3, $4, $5, $6::jsonb, $7, coalesce(($8::text)::timestamptz, now()))""",
            ids["memory"],
            tenant,
            PROFILE_ID,
            status,
            reviewer,
            json.dumps(provenance),
            project,
            src.get("created_at"),
        )
        await conn.execute(
            """insert into agent_memory_revisions (id, memory_id, title, content, applies_when, guidance, avoid_when, author)
               values ($1, $2, $3, $4, $5, $6, $7, $8)""",
            ids["revision"],
            ids["memory"],
            draft["title"],
            c["content"],
            draft["applies_when"],
            draft["guidance"],
            draft.get("avoid_when"),
            AUTHOR,
        )
        await conn.execute(
            "update agent_memories set current_revision_id = $1, index_enqueued_at = case when $2::boolean then now() end where id = $3",
            ids["revision"],
            active,
            ids["memory"],
        )
        await conn.execute(
            """insert into agent_memory_proposals
                 (id, tenant_id, profile_id, kind, status, proposed_memory_id, reasoning, producer_key,
                  reviewed_by_user_id, reviewed_at, project_id, created_at)
               values ($1, $2, $3, 'create', $4, $5, $6::jsonb, $7, $8, ($9::text)::timestamptz, $10, coalesce(($11::text)::timestamptz, now()))""",
            ids["proposal"],
            tenant,
            PROFILE_ID,
            "accepted" if active else "pending",
            ids["memory"],
            json.dumps(reasoning) if reasoning else None,
            f"{AUTHOR}:{src['id']}",
            reviewer,
            src.get("resolved_at") if active else None,
            project,
            src.get("created_at"),
        )


# ---------------------------------------------------------------- verify / undo


def memory_exists(memory_id: str):
    async def check(conn) -> bool:
        return bool(
            await conn.fetchval("select 1 from agent_memories where id = $1::uuid", memory_id)
        )

    return check


def exported_ids(bundle: Path) -> list[dict]:
    """Every memory this bundle could have imported, converted now or not: what undo must reach."""
    return [ids_for(i["memory"]["id"]) for i in read_jsonl(bundle / "memories_source.jsonl")]


def converted_ids(bundle: Path) -> list[dict]:
    return [
        ids_for(r["legacy_id"])
        for r in read_jsonl(bundle / "memories_converted.jsonl")
        if r.get("draft")
    ]


async def verify_memories(args):
    bundle = Path(args.bundle)
    sources = [i["memory"] for i in read_jsonl(bundle / "memories_source.jsonl")]
    want = {"active": 0, "pending": 0}
    conv = {
        r["legacy_id"] for r in read_jsonl(bundle / "memories_converted.jsonl") if r.get("draft")
    }
    for s in sources:
        if s["id"] in conv:
            want[MOVING[s["status"]]] += 1
    mem_ids = [i["memory"] for i in converted_ids(bundle)]
    conn = await connect(args.db)
    try:
        got = {
            r["status"]: r["n"]
            for r in await conn.fetch(
                "select status, count(*) n from agent_memories where id = any($1::uuid[]) and tenant_id = $2 and project_id = $3 group by 1",
                mem_ids,
                args.tenant,
                args.project,
            )
        }
        broken = await conn.fetchval(
            """select count(*) from agent_memories m
               left join agent_memory_proposals p on p.proposed_memory_id = m.id
               where m.id = any($1::uuid[]) and (
                 m.current_revision_id is null or p.id is null
                 or (m.status = 'active' and (m.index_enqueued_at is null and not exists
                      (select 1 from agent_memory_embeddings e where e.memory_id = m.id)))
                 or (m.status = 'active' and p.status <> 'accepted')
                 or (m.status = 'pending' and p.status <> 'pending'))""",
            mem_ids,
        )
        embedded = await conn.fetchval(
            "select count(distinct memory_id) from agent_memory_embeddings where memory_id = any($1::uuid[])",
            mem_ids,
        )
    finally:
        await conn.close()
    ok = True
    for s in ("active", "pending"):
        n = got.get(s, 0)
        ok &= n == want[s]
        print(
            f"  {s:8} target {n:>5}  expected {want[s]:>5}  {'ok' if n == want[s] else 'MISMATCH'}"
        )
    print(
        f"  incomplete rows: {broken} (want 0); embedded so far: {embedded} of {want['active']} live"
    )
    ok &= broken == 0
    print("VERIFIED" if ok else "NOT VERIFIED")
    if not ok:
        sys.exit(1)


async def undo_memories(args):
    """Clear the labels first (unlabel-memories): they live in the app database and need the memory to exist."""
    ids = exported_ids(Path(args.bundle))
    proposals, memories = [i["proposal"] for i in ids], [i["memory"] for i in ids]
    ours = "id = any($1::uuid[]) and tenant_id = $2 and project_id = $3"
    session = Session(args.db, CLAIM)
    conn = await session.open()
    try:
        if args.dry_run:
            p = await conn.fetchval(
                f"select count(*) from agent_memory_proposals where {ours}",
                proposals,
                args.tenant,
                args.project,
            )
            m = await conn.fetchval(
                f"select count(*) from agent_memories where {ours}",
                memories,
                args.tenant,
                args.project,
            )
            print(f"dry run: would delete {p} proposals and {m} memories")
            return
        async with conn.transaction():
            p = await conn.execute(
                f"delete from agent_memory_proposals where {ours}",
                proposals,
                args.tenant,
                args.project,
            )
            m = await conn.execute(
                f"delete from agent_memories where {ours}", memories, args.tenant, args.project
            )
    except Exception as e:  # one transaction: nothing or everything is deleted
        if not outside_problem(e):
            raise
        print(f"STOPPED: {type(e).__name__}: {e}. Nothing was deleted; rerun to finish.")
        sys.exit(3)
    finally:
        await session.close()
    print(
        f"deleted {p.split()[-1]} proposals and {m.split()[-1]} memories (revisions and embeddings went with them)"
    )


def add_commands(sub):
    e = sub.add_parser("export-memories")
    e.add_argument("--db", help="old agents DB (else POSTGRES_CONFIG__*)")
    e.add_argument("--out", required=True, help="bundle folder")

    c = sub.add_parser("convert-memories")
    c.add_argument("--bundle", required=True)
    c.add_argument(
        "--model",
        help="e.g. anthropic-foundry:claude-opus-4-8 (else AGENT_CONFIG__MODEL_PROVIDER_DEFAULT)",
    )
    c.add_argument(
        "--agents-py", help="agents-py root to import from (else AGENTS_PY_ROOT or /app)"
    )
    c.add_argument("--concurrency", type=int, default=8, help="memories converted at once")
    c.add_argument(
        "--attempts",
        type=int,
        default=3,
        help="tries per memory, with backoff, for rate limits and errors",
    )
    c.add_argument(
        "--retries",
        type=int,
        default=3,
        help="tries the model gets to fix output that breaks MemoryDraft (the app's generator uses 3)",
    )
    c.add_argument("--only", help="comma-separated legacy memory ids")
    c.add_argument(
        "--force", action="store_true", help="convert the selected memories again (others are kept)"
    )
    c.add_argument(
        "--fake",
        choices=["ok", "flaky", "slow", "ratelimit", "leaky"],
        help="use a stand-in model (tests only)",
    )

    a = sub.add_parser("accept-memories")
    a.add_argument("--bundle", required=True)
    a.add_argument(
        "--ids",
        required=True,
        help="comma-separated legacy memory ids (the first 8 characters are enough)",
    )

    for name in ("import-memories", "verify-memories", "undo-memories"):
        s = sub.add_parser(name)
        s.add_argument("--bundle", required=True)
        s.add_argument("--db", help="new agents DB (else POSTGRES_CONFIG__*)")
        s.add_argument("--tenant", required=True)
        s.add_argument("--project", required=True)
        if name != "verify-memories":
            s.add_argument("--dry-run", action="store_true")
    sub.choices["import-memories"].add_argument(
        "--user-map", help="CSV with old_user_id,new_user_id"
    )
    sub.choices["import-memories"].add_argument("--report")


COMMANDS = {
    "export-memories": export_memories,
    "convert-memories": convert_memories,
    "accept-memories": accept_memories,
    "import-memories": import_memories,
    "verify-memories": verify_memories,
    "undo-memories": undo_memories,
}
