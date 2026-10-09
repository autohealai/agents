#!/usr/bin/env python3
"""Generate catalog.json from every agents/<name>/agent.yaml.

catalog.json is the single machine-readable index that powers the gallery today
and the one-click import flow later. It is a GENERATED file — do not hand-edit
it. Run this script and commit the result; CI fails if it is stale.

Each record carries the metadata needed to render a card (name, summary,
category, trigger, safety, required integrations) plus the full agent.yaml text
embedded inline, so the gallery's "Copy agent.yaml" button and any future import
endpoint need no extra network fetch.
"""
import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO_ROOT / "agents"
OUTPUT = REPO_ROOT / "catalog.json"
RAW_BASE = "https://raw.githubusercontent.com/autohealai/agents/main"
BLOB_BASE = "https://github.com/autohealai/agents/blob/main"


def build_record(spec: Path) -> dict:
    name = spec.parent.name
    text = spec.read_text()
    doc = yaml.safe_load(text)
    # An apiVersion document keeps its catalog fields in catalog.yaml beside it:
    # the platform rejects any key it does not define.
    catalog = spec.parent / "catalog.yaml"
    if "apiVersion" in doc and catalog.exists():
        meta = yaml.safe_load(catalog.read_text()) or {}
    else:
        meta = doc.get("metadata") or {}
    requires = meta.get("requires") or {}

    readme = spec.parent / "README.md"
    rel_dir = f"agents/{name}"

    return {
        "name": name,
        "display_name": meta.get("display_name") or doc.get("display_name") or name,
        # Prefer the short card summary; fall back to the full description.
        "summary": meta.get("summary") or doc.get("description") or "",
        "description": doc.get("description") or "",
        "category": meta.get("category"),
        "trigger": meta.get("trigger"),
        "safety": meta.get("safety"),
        "requires": {"integrations": requires.get("integrations", [])},
        "github_url": f"{BLOB_BASE}/{rel_dir}/agent.yaml",
        "raw_url": f"{RAW_BASE}/{rel_dir}/agent.yaml",
        "readme_url": f"{BLOB_BASE}/{rel_dir}/README.md" if readme.exists() else None,
        # Embedded so the gallery can copy without a cross-origin fetch.
        "yaml": text,
    }


def main() -> int:
    specs = sorted(AGENTS_DIR.glob("*/agent.yaml"))
    if not specs:
        print("No agents found under agents/*/agent.yaml")
        return 1

    catalog = {
        "generated_by": "scripts/build_catalog.py",
        "catalog_schema_version": 1,
        "agents": [build_record(spec) for spec in specs],
    }

    OUTPUT.write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"
    )
    print(f"Wrote {OUTPUT.relative_to(REPO_ROOT)} with {len(specs)} agent(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
