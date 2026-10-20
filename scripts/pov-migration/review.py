"""review-memories: one HTML page to read every converted memory next to its old lesson.

Held drafts show the details they added, highlighted. With --previous (an earlier
memories_converted.jsonl), each card also shows that run's draft and is tagged when it changed.
The page is self-contained, so it opens offline.
"""

import html
import json
import re
from pathlib import Path

from db import read_jsonl

esc = html.escape


def _draft(r: dict | None) -> dict | None:
    if not r:
        return None
    return r.get("draft") or (r.get("rejected") or {}).get("draft")


def _mark(text: str | None, words) -> str:
    out = esc(text or "")
    for w in sorted(words, key=len, reverse=True):
        out = re.sub(re.escape(esc(w)), lambda m: f"<mark>{m.group(0)}</mark>", out, flags=re.I)
    return out


def _block(label: str, d: dict | None, added=()) -> str:
    if not d:
        return ""
    avoid = d.get("avoid_when")
    return f"""<div class="col"><div class="label">{label}</div><div class="title">{_mark(d["title"], added)}</div>
      <dl><dt>Use when</dt><dd>{_mark(d["applies_when"], added)}</dd>
      <dt>What to do</dt><dd>{_mark(d["guidance"], added)}</dd>
      <dt>Avoid when</dt><dd class="{"" if avoid else "none"}">{_mark(avoid, added) if avoid else "not set"}</dd></dl></div>"""


def trigger_html(m: dict) -> str:
    trigger = (m.get("source_metadata") or {}).get("trigger")
    return (
        f'<p class="when">When it applies: {esc(trigger)}</p>'
        if isinstance(trigger, str) and trigger.strip()
        else ""
    )


def build(bundle: Path, previous: Path | None) -> tuple[str, dict]:
    sources = {i["memory"]["id"]: i["memory"] for i in read_jsonl(bundle / "memories_source.jsonl")}
    rows = read_jsonl(bundle / "memories_converted.jsonl")
    prev = {r["legacy_id"]: r for r in read_jsonl(previous)} if previous else {}
    counts = {"ok": 0, "held": 0, "failed": 0, "retried": 0, "avoid": 0, "changed": 0}
    cards = []
    order = {"held": 0, "failed": 1, "ok": 2}
    for r in sorted(
        rows,
        key=lambda r: (
            order["ok" if r.get("draft") else "held" if r.get("rejected") else "failed"],
            r["legacy_id"],
        ),
    ):
        m = sources.get(r["legacy_id"])
        if not m:
            continue
        state = "ok" if r.get("draft") else "held" if r.get("rejected") else "failed"
        d, added = _draft(r), (r.get("rejected") or {}).get("added", [])
        old = _draft(prev.get(r["legacy_id"]))
        changed = bool(prev) and old != d
        tags = (
            [state]
            + ["retried"] * bool(r.get("model_retries"))
            + ["avoid"] * bool(d and d.get("avoid_when"))
            + ["changed"] * changed
        )
        for t in tags:
            counts[t] += 1
        reason = ""
        if state == "held":
            reason = f'<div class="reason">Adds details the lesson never mentions: <b>{esc(", ".join(added))}</b></div>'
        elif state == "failed":
            reason = f'<div class="reason">{esc(r.get("error", ""))}</div>'
        cols = f"""<div class="col old"><div class="label">Old lesson ({esc(str(m.get("status", "")))})</div>
          <div class="title">{esc(m["title"])}</div>{trigger_html(m)}<p>{esc(m["content"])}</p></div>"""
        cols += _block(
            "New memory" if state == "ok" else "Held draft" if state == "held" else "Draft",
            d,
            added,
        )
        if prev:
            cols += (
                _block("Previous run" + (" (changed)" if changed else ""), old)
                or '<div class="col"><div class="label">Previous run</div><p class="none">no draft</p></div>'
            )
        search = " ".join([r["legacy_id"], m["title"], m["content"], json.dumps(d or {})]).lower()
        chip = {"ok": "Converted", "held": "Held for review", "failed": "Failed"}[state]
        cards.append(f"""<article class="card" data-tags="{" ".join(tags)}" data-search="{esc(search)}">
      <header><span class="chip {state}">{chip}</span><code>{esc(r["legacy_id"][:8])}</code>
      {'<span class="chip changed">Changed</span>' if changed else ""}</header>{reason}
      <div class="cols {"three" if prev else ""}">{cols}</div></article>""")
    total = len(cards)
    buttons = [
        ("all", f"All {total}"),
        ("held", f"Held {counts['held']}"),
        ("failed", f"Failed {counts['failed']}"),
        ("retried", f"Retried {counts['retried']}"),
        ("avoid", f"Has Avoid when {counts['avoid']}"),
    ]
    if prev:
        buttons.append(("changed", f"Changed {counts['changed']}"))
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Memory Conversion Review</title>
<style>
:root {{ --bg:#f7f7f5; --card:#fff; --ink:#0a162a; --muted:#5b6472; --line:#e3e3df; --ok:#2f6f4f; --okbg:#e8f2ec;
  --held:#8a5a00; --heldbg:#fbf1dc; --fail:#9b2c2c; --failbg:#f9e5e5; --accent:#3a5bd9; --accentbg:#e9eefc; --mark:#ffe08a; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#0d1117; --card:#151b24; --ink:#e6e9ef; --muted:#9aa4b2; --line:#273041;
  --okbg:#16301f; --ok:#7cc79a; --heldbg:#33270c; --held:#e4b75c; --failbg:#3a1717; --fail:#f08b8b; --accentbg:#1b2442;
  --accent:#93a8ff; --mark:#6b5410; }} }}
* {{ box-sizing:border-box; }} body {{ margin:0; background:var(--bg); color:var(--ink); font:15px/1.5 system-ui, sans-serif; }}
main {{ max-width:1280px; margin:0 auto; padding:24px 16px 64px; }} h1 {{ font-size:24px; margin:0 0 8px; }}
.bar {{ position:sticky; top:0; background:var(--bg); padding:8px 0; display:flex; flex-wrap:wrap; gap:8px; }}
.bar button {{ font:inherit; border:1px solid var(--line); background:var(--card); color:var(--ink); border-radius:999px; padding:4px 12px; cursor:pointer; }}
.bar button.on {{ background:var(--accentbg); border-color:var(--accent); color:var(--accent); }}
.bar input {{ flex:1; min-width:180px; font:inherit; padding:4px 12px; border:1px solid var(--line); border-radius:999px; background:var(--card); color:var(--ink); }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px 16px; margin:12px 0; }}
header {{ display:flex; gap:8px; align-items:center; margin-bottom:8px; }} code {{ color:var(--muted); font-size:13px; }}
.chip {{ font-size:12px; font-weight:600; border-radius:999px; padding:2px 10px; }}
.chip.ok {{ background:var(--okbg); color:var(--ok); }} .chip.held {{ background:var(--heldbg); color:var(--held); }}
.chip.failed {{ background:var(--failbg); color:var(--fail); }} .chip.changed {{ background:var(--accentbg); color:var(--accent); }}
.reason {{ background:var(--heldbg); color:var(--held); border-radius:8px; padding:6px 10px; margin-bottom:8px; font-size:14px; }}
.cols {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }} .cols.three {{ grid-template-columns:1fr 1fr 1fr; }}
@media (max-width:900px) {{ .cols, .cols.three {{ grid-template-columns:1fr; }} }}
.col {{ min-width:0; overflow-wrap:anywhere; }} .col.old {{ color:var(--muted); }}
.label {{ font-size:12px; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); margin-bottom:4px; }}
.when {{ font-style:italic; margin-bottom:4px; }} .title {{ font-weight:600; color:var(--ink); margin-bottom:4px; }} p {{ margin:0; }} dl {{ margin:0; }}
dt {{ font-size:12px; color:var(--muted); margin-top:6px; }} dd {{ margin:0; }} .none {{ color:var(--muted); font-style:italic; }}
mark {{ background:var(--mark); color:inherit; border-radius:3px; padding:0 2px; }}
</style></head><body><main><h1>Memory conversion review</h1>
<p>{counts["ok"]} converted, {counts["held"]} held for review, {counts["failed"]} failed. Held drafts added details the
lesson never mentions; they are highlighted. Keep one with <code>accept-memories</code>, or reconvert it with
<code>convert-memories --only</code>.</p>
<div class="bar">{"".join(f'<button data-f="{k}"{" class=on" if k == "all" else ""}>{v}</button>' for k, v in buttons)}
<input type="search" placeholder="Search titles, text or id"></div>
{"".join(cards)}</main><script>
const bs = document.querySelectorAll('.bar button'), q = document.querySelector('.bar input'); let f = 'all';
function apply() {{ const s = q.value.trim().toLowerCase(); document.querySelectorAll('.card').forEach(c => {{
  c.style.display = (f === 'all' || c.dataset.tags.split(' ').includes(f)) && (!s || c.dataset.search.includes(s)) ? '' : 'none'; }}); }}
bs.forEach(b => b.onclick = () => {{ bs.forEach(x => x.classList.remove('on')); b.classList.add('on'); f = b.dataset.f; apply(); }});
q.oninput = apply;
</script></body></html>"""
    return page, counts


async def review_memories(args):
    page, counts = build(Path(args.bundle), Path(args.previous) if args.previous else None)
    Path(args.out).write_text(page)
    print(
        f"wrote {args.out}: {counts['ok']} converted, {counts['held']} held, {counts['failed']} failed"
        + (f", {counts['changed']} changed since the previous run" if args.previous else "")
    )


def add_commands(sub):
    r = sub.add_parser(
        "review-memories", help="HTML page: old lesson next to each converted memory"
    )
    r.add_argument("--bundle", required=True)
    r.add_argument("--out", required=True, help="where to write the .html page")
    r.add_argument("--previous", help="an earlier memories_converted.jsonl to compare with")


COMMANDS = {"review-memories": review_memories}
