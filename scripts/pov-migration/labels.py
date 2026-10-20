"""Labels for migrated memories, built from the old memories' subject tags.

label-memories    PUT each imported memory's labels through the app's API (labels live in the
                  app database). Import the memories first. --dry-run prints the plan.
verify-labels     GET each memory's labels and compare them with the plan.
unlabel-memories  clear them. Run this BEFORE undo-memories: a deleted memory's labels
                  can no longer be reached through the API.

The old classifier tagged each memory with subjects {kind, key}. They become labels:
  product      -> domain, only through the label map's product_domains (unlisted: no domain, and listed)
  integration  -> integration, minus generic categories, with aliases folded
  team, service -> team, service
  platform     -> no label
A customer's label map (--label-map, JSON) adds their product families and aliases;
see label-maps/example.json. Runs from a laptop with the user's token, like push-skills.
"""

import json
import sys
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from api import Stop, api_args, call_with_retry, stops_cleanly, target
from db import read_jsonl
from memories import ids_for

# Generic categories the classifier used instead of a tool name.
DROP_INTEGRATIONS = {"monitoring-tool", "ticketing-system", "patch-management-tool", "api-gateway"}
# Dynatrace's own product names for parts of one integration.
FOLD_INTEGRATIONS = {"grail": "dynatrace", "bizevents": "dynatrace", "dynatrace-davis": "dynatrace"}


def kebab(v: str) -> str:
    return v.strip().lower().replace("_", "-").replace(" ", "-")


def load_label_map(path: str | None) -> dict:
    """{"product_domains": {product: domain or null}, "drop_integrations": [...], "fold_integrations": {alias: name}}"""
    raw = json.loads(Path(path).read_text()) if path else {}
    unknown = set(raw) - {"product_domains", "drop_integrations", "fold_integrations", "_comment"}
    if unknown:
        sys.exit(f"label map: unknown keys {sorted(unknown)}")
    return {
        "product_domains": {
            kebab(k): (kebab(v) if v else None) for k, v in raw.get("product_domains", {}).items()
        },
        "drop_integrations": DROP_INTEGRATIONS
        | {kebab(v) for v in raw.get("drop_integrations", [])},
        "fold_integrations": FOLD_INTEGRATIONS
        | {kebab(k): kebab(v) for k, v in raw.get("fold_integrations", {}).items()},
    }


def labels_for(memory: dict, label_map: dict, unmapped: Counter) -> dict[str, list[str]]:
    """Labels for one memory. Counts in unmapped each product the map does not list (it gets no domain)."""
    md = memory.get("source_metadata") or {}
    classification = md.get("classification") if isinstance(md.get("classification"), dict) else {}
    domains = label_map["product_domains"]
    out: dict[str, set] = {}
    for s in classification.get("subjects") or []:
        if not (isinstance(s, dict) and s.get("kind") and s.get("key")):
            continue
        kind, key = s["kind"], kebab(s["key"])
        if kind == "product" or (
            kind == "integration" and domains.get(key)
        ):  # a product filed as an integration
            if key not in domains:
                unmapped[key] += 1
            if domain := domains.get(key):  # unlisted, or null in the map: no domain
                out.setdefault("domain", set()).add(domain)
        elif kind == "integration":
            if key not in label_map["drop_integrations"]:
                out.setdefault("integration", set()).add(
                    label_map["fold_integrations"].get(key, key)
                )
        elif kind in ("team", "service"):
            out.setdefault(kind, set()).add(key)
    return {k: sorted(v) for k, v in out.items()}


def plan(bundle: Path, label_map: dict) -> tuple[dict[str, dict], Counter, list]:
    """Memory id on the new install -> its labels, for every converted (so imported) memory."""
    sources = {i["memory"]["id"]: i["memory"] for i in read_jsonl(bundle / "memories_source.jsonl")}
    converted = read_jsonl(bundle / "memories_converted.jsonl")
    unmapped = Counter()
    out, titles = {}, []
    for c in converted:
        if c.get("draft"):
            m = sources[c["legacy_id"]]
            mid = ids_for(m["id"])["memory"]
            out[mid] = labels_for(m, label_map, unmapped)
            titles.append((mid, m["title"]))
    return out, unmapped, titles


def current(t, mid: str, project: str):
    status, body = call_with_retry(
        t, "GET", f"/api/v1/labels/memories/{mid}", {"project_id": project}
    )
    if status != 200:
        return status, body
    return status, {k: sorted(v) for k, v in ((body or {}).get("labels") or {}).items()}


def run_parallel(items, fn, concurrency: int, every: int, describe):
    """Run fn over items on a thread pool; Stop from any call cancels the rest and re-raises."""
    lock, counts, done = threading.Lock(), Counter(), [0]

    def one(item):
        outcome = fn(item)
        with lock:
            counts[outcome[0]] += 1
            done[0] += 1
            if done[0] % every == 0:
                print(f"  {done[0]}/{len(items)} checked: {describe(counts)}")
        return outcome

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(one, i) for i in items]
        results = []
        try:
            for f in futures:
                results.append(f.result())
        except Stop:
            for f in futures:
                f.cancel()
            raise
    return results, counts


def label_memories(args):
    want, unmapped, titles = plan(Path(args.bundle), load_label_map(args.label_map))
    keys = Counter(k for labels in want.values() for k in labels)
    print(
        f"{len(want)} imported memories; with at least one label: {sum(1 for v in want.values() if v)}"
    )
    for k in ("domain", "service", "integration", "team"):
        print(f"  {k:12} on {keys.get(k, 0)} memories")
    if unmapped:
        print(
            f"  products not in the label map (no domain label until you add them): {dict(unmapped)}"
        )
    if args.dry_run:
        for mid, title in titles[: args.show]:
            print(f"  {title[:60]:60} {json.dumps(want[mid])}")
        print("dry run, nothing written")
        return
    if not (args.domain and args.project):
        sys.exit("a real run needs --domain and --project")
    t = target(args)

    def apply(item):
        mid, labels = item
        status, have = current(t, mid, args.project)
        if status != 200:  # 404: the memory is not imported into this project
            return "failed", mid, f"read {status}: {json.dumps(have)[:200]}"
        if have == labels:
            return "matching", mid, None
        status, body = call_with_retry(
            t,
            "PUT",
            f"/api/v1/labels/memories/{mid}",
            {"project_id": args.project},
            {"labels": labels},
        )
        return (
            ("written", mid, None)
            if status == 200
            else ("failed", mid, f"write {status}: {json.dumps(body)[:200]}")
        )

    results, counts = run_parallel(
        list(want.items()),
        apply,
        args.concurrency,
        100,
        lambda c: f"{c['written']} written, {c['matching']} matching, {c['failed']} failed",
    )
    print(
        f"written {counts['written']}, already matching {counts['matching']}, failed {counts['failed']}"
    )
    for state, mid, why in results:
        if state == "failed":
            print(f"  FAILED {mid}: {why}")
    if counts["failed"]:
        sys.exit(1)


def verify_labels(args):
    want, _, _ = plan(Path(args.bundle), load_label_map(args.label_map))
    t = target(args)

    def check(item):
        mid, labels = item
        status, have = current(t, mid, args.project)
        return (
            ("ok", mid, None)
            if status == 200 and have == labels
            else ("bad", mid, f"want {labels}, got {status} {have}")
        )

    results, counts = run_parallel(
        list(want.items()), check, args.concurrency, 100, lambda c: f"{c['bad']} mismatched"
    )
    for state, mid, why in results:
        if state == "bad":
            print(f"  MISMATCH {mid}: {why}")
    print(f"{counts['ok']} of {len(want)} match")
    print("VERIFIED" if not counts["bad"] else "NOT VERIFIED")
    if counts["bad"]:
        sys.exit(1)


def unlabel_memories(args):
    # Every exported memory, converted now or not: one imported earlier may have been reconverted since.
    source = read_jsonl(Path(args.bundle) / "memories_source.jsonl")
    want = {ids_for(i["memory"]["id"])["memory"]: {} for i in source}
    t = target(args)

    def clear(item):
        mid, _ = item
        status, have = current(t, mid, args.project)
        if status == 404:
            return "unreachable", mid, None
        if status == 200 and not have:
            return "empty", mid, None
        if args.dry_run:
            return "cleared", mid, None
        status, _ = call_with_retry(
            t, "PUT", f"/api/v1/labels/memories/{mid}", {"project_id": args.project}, {"labels": {}}
        )
        return ("cleared", mid, None) if status == 200 else ("unreachable", mid, f"status {status}")

    results, counts = run_parallel(
        list(want.items()), clear, args.concurrency, 100, lambda c: f"{c['cleared']} cleared"
    )
    verb = "would clear" if args.dry_run else "cleared"
    print(
        f"{verb} {counts['cleared']}, already empty {counts['empty']}, unreachable {counts['unreachable']}"
    )
    gone = [mid for state, mid, _ in results if state == "unreachable"]
    if gone:
        print("  unreachable (memory gone, or not in this project):", gone[:5])


def add_commands(sub):
    for name in ("label-memories", "verify-labels", "unlabel-memories"):
        s = sub.add_parser(name)
        api_args(s, required=name != "label-memories")
        s.add_argument("--bundle", required=True)
        s.add_argument("--project", required=name != "label-memories")
        s.add_argument(
            "--label-map",
            help="customer label map JSON (see label-maps/); default: no product families",
        )
        s.add_argument(
            "--concurrency",
            type=int,
            default=8,
            help="API calls in flight (each takes about 1 s over the internet)",
        )
        if name != "verify-labels":
            s.add_argument("--dry-run", action="store_true")
    sub.choices["label-memories"].add_argument(
        "--show", type=int, default=5, help="examples to print in a dry run"
    )


COMMANDS = {
    "label-memories": stops_cleanly(label_memories),
    "verify-labels": stops_cleanly(verify_labels),
    "unlabel-memories": stops_cleanly(unlabel_memories),
}
