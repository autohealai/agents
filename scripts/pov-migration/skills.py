"""Skills: old agents.md sections and runbooks -> Git-backed skills on the new install.

probe          what the token can reach on the target (tenant, project, Git repository, routes)
export-skills  old agents DB -> one SKILL.md per skill (no network)
push-skills    commit those files to a project through the Git registry API, in one commit
"""

import json
import re
import shutil
import sys
import uuid
from pathlib import Path

from api import api_args, call_with_retry, stops_cleanly, target
from db import columns_of, connect, require_columns

SKIP_SECTIONS = {
    "app-readme": "duplicate of architecture-overview",
    "investigation-steps": "added by hand to the agent's system prompt",
}
LABEL_SOURCE = "pov-migration"
SOURCE_COLUMNS = {
    "agentsmd_latest_sections": ["section_id"],
    "agentsmd_sections": ["id", "name", "title", "content", "section_type", "is_custom"],
    "runbooks_latest": ["runbook_id"],
    "runbooks": ["id", "name", "title", "content", "frontmatter"],
}


def probe(args):
    t = target(args, need_minutes=0)
    status, me = call_with_retry(t, "GET", "/api/v1/whoami")
    print(f"whoami                   {status} roles={me.get('roles') if status == 200 else me}")
    status, projects = call_with_retry(t, "GET", "/api/v1/projects")
    ids = [p["id"] for p in (projects or {}).get("items", [])] if status == 200 else []
    print(f"projects                 {status} {ids}")
    if args.project:
        if args.project not in ids:
            print(
                f"STOPPED: project {args.project!r} is not visible to this token; check its id or your access"
            )
            sys.exit(2)
        status, repo = call_with_retry(
            t, "GET", "/api/v1/git-registry/repository", {"project_id": args.project}
        )
        shown = (repo.get("storage_kind"), repo.get("default_branch")) if status == 200 else repo
        print(f"git repository           {status} {shown}")
    for label, path in (
        ("agent memories route", "/api/agent-memories"),
        ("labels route", "/api/v1/labels/keys"),
    ):
        status, body = call_with_retry(t, "GET", path, {"project_id": args.project})
        routed = "NOT JSON, likely unrouted" if "_non_json" in (body or {}) else "ok"
        print(f"{label:24} {status} {routed}")


def slug(s: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")


def skill_md(name: str, description: str | None, kind: str, body: str) -> str:
    lines = ["---", f"name: {json.dumps(name)}"]
    if description:
        lines.append(f"description: {json.dumps(description)}")
    lines += ["labels:", f"  kind: {kind}", f"  source: {LABEL_SOURCE}", "---"]
    return "\n".join(lines) + "\n\n" + body.strip() + "\n"


async def export_skills(args):
    final = Path(args.out) / "skills"
    if final.exists():
        sys.exit(f"{final} already holds a skills export; use a fresh folder")
    out = Path(args.out) / ".skills.partial"  # renamed to skills/ only once complete
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    conn = await connect(args.source_db)
    try:
        await require_columns(conn, SOURCE_COLUMNS)
        # Older installs keep every section tenant-wide and have no profile_id column.
        profile = (
            "l.profile_id"
            if "profile_id" in await columns_of(conn, "agentsmd_latest_sections")
            else "null::text"
        )
        sections = await conn.fetch(
            f"""select s.name, s.title, s.content, s.section_type, s.is_custom, {profile} as profile_id
                from agentsmd_latest_sections l join agentsmd_sections s on s.id = l.section_id
                where coalesce(s.content, '') <> '' order by s.name"""
        )
        runbooks = await conn.fetch(
            """select r.name, r.title, r.content, r.frontmatter
               from runbooks_latest l join runbooks r on r.id = l.runbook_id order by r.name"""
        )
    finally:
        await conn.close()

    written, skipped = [], []

    def write(skill_id: str, md: str):
        unique, n = skill_id, 1
        while (out / unique).exists():  # two names that slug alike: the later one gets -2, -3, ...
            n += 1
            unique = f"{skill_id}-{n}"
        if unique != skill_id:
            print(f"  {skill_id!r} is taken; writing this one as {unique!r}")
        path = out / unique / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(md)
        written.append(unique)

    for s in sections:
        if s["profile_id"]:
            skipped.append((s["name"], f"addition for profile {s['profile_id']}, not mapped"))
        elif s["name"] in SKIP_SECTIONS:
            skipped.append((s["name"], SKIP_SECTIONS[s["name"]]))
        elif s["section_type"] == "integration":
            write(slug(s["name"]), skill_md(s["title"], None, "integration-guide", s["content"]))
        elif s["name"] == "architecture-overview":
            write("architecture-overview", skill_md(s["title"], None, "architecture", s["content"]))
        elif s["is_custom"]:
            write(slug(s["name"]), skill_md(s["title"], None, "custom-skill", s["content"]))
        else:
            skipped.append((s["name"], f"built-in {s['section_type']} section, no Git home"))

    for r in runbooks:
        fm = r["frontmatter"]
        fm = json.loads(fm) if isinstance(fm, str) else fm
        desc = fm.get("description") if isinstance(fm, dict) else None
        title = (r["title"] or r["name"]).strip().strip('"').strip()
        write(slug(r["name"]), skill_md(title, desc, "custom-skill", r["content"]))

    out.rename(final)
    print(f"wrote {len(written)} skills to {final}")
    for name, why in skipped:
        print(f"  skipped {name}: {why}")


def push_skills(args):
    files = sorted(Path(args.dir, "skills").glob("*/SKILL.md"))
    if not files:
        sys.exit(f"no skills under {args.dir}/skills")
    t = target(args)
    q = {"project_id": args.project}

    status, repo = call_with_retry(t, "GET", "/api/v1/git-registry/repository", q)
    if status != 200:
        sys.exit(f"repository: {status} {repo}")
    branch = args.branch or repo["default_branch"]
    print(f"project {args.project}: branch {branch}, storage {repo.get('storage_kind')}")

    status, tree = call_with_retry(
        t, "GET", "/api/v1/git-registry/tree", {**q, "branch": branch, "path": "skills"}
    )
    existing = {e["name"] for e in tree.get("entries", [])} if status == 200 else set()

    todo = []
    for f in files:
        skill_id = f.parent.name
        if skill_id in existing:
            print(f"  exists, skipped: {skill_id}")
        else:
            todo.append((skill_id, f.read_text()))
    if args.dry_run or not todo:
        for skill_id, _ in todo:
            print(f"  would create: skills/{skill_id}/SKILL.md")
        print(f"{len(todo)} to create" + (" (dry run, nothing written)" if args.dry_run else ""))
        return

    status, draft = call_with_retry(t, "GET", "/api/v1/git-registry/draft", {**q, "branch": branch})
    if status != 200:
        sys.exit(f"draft: {status} {draft}")
    version, head = draft["context"]["draft_version"], draft["context"]["branch_head"]
    paths = []
    for skill_id, content in todo:
        path = f"skills/{skill_id}/SKILL.md"
        body = {
            "branch": branch,
            "path": path,
            "content": content,
            "expected_draft_version": version,
        }
        status, saved = call_with_retry(t, "PUT", "/api/v1/git-registry/file", q, body)
        if status != 200:
            sys.exit(
                f"save {path}: {status} {saved}\nsaved so far, in the draft and not committed: {paths}\n"
                "rerun to finish (saved files are rewritten), or discard the draft in the web editor"
            )
        version, head = saved["context"]["draft_version"], saved["context"]["branch_head"]
        paths.append(path)
        print(f"  saved {path}")

    body = {
        "branch": branch,
        "paths": paths,
        "message": f"Migrate {len(paths)} skills from the POV install",
        "expected_head": head,
        "expected_draft_version": version,
        "idempotency_key": str(uuid.uuid4()),
    }
    status, commit = call_with_retry(t, "POST", "/api/v1/git-registry/commits", q, body)
    if status not in (200, 201, 202):
        sys.exit(
            f"commit: {status} {commit}\nthe files sit in the shared draft; commit or discard them in the web editor"
        )
    print(
        f"committed {len(paths)} skills: {(commit.get('commit') or {}).get('sha') or commit.get('state')}"
    )


def add_commands(sub):
    p = sub.add_parser("probe", help="what the token can reach on the target")
    api_args(p)
    p.add_argument("--project", help="also check this project is visible and has a Git repository")

    e = sub.add_parser("export-skills", help="old agents DB -> SKILL.md files")
    e.add_argument("--source-db", required=True, help="postgresql://... of the old agents DB")
    e.add_argument("--out", required=True, help="a fresh folder")

    s = sub.add_parser("push-skills", help="commit the exported skills to a project")
    api_args(s)
    s.add_argument("--project", required=True)
    s.add_argument("--dir", required=True, help="the folder export-skills wrote")
    s.add_argument("--branch", help="defaults to the repository's default branch")
    s.add_argument("--dry-run", action="store_true")


COMMANDS = {
    "probe": stops_cleanly(probe),
    "export-skills": export_skills,
    "push-skills": stops_cleanly(push_skills),
}
