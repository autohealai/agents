#!/usr/bin/env python3
"""Validate every agents/<name>/agent.yaml in the repo.

Keeps the contribution bar low but the repo safe: valid YAML, required fields
present, name well-formed, name matches its folder, and names unique. Exits
non-zero on any problem so CI blocks the PR.
"""
import re
import sys
from pathlib import Path

import yaml

NAME_RE = re.compile(r"^[a-z0-9_-]+$")
REQUIRED = ["schema_version", "name", "description", "instructions"]
AGENTS_DIR = Path(__file__).resolve().parent.parent / "agents"


def main() -> int:
    errors: list[str] = []
    seen: dict[str, str] = {}

    specs = sorted(AGENTS_DIR.glob("*/agent.yaml"))
    if not specs:
        print("No agents found under agents/*/agent.yaml")
        return 1

    for spec in specs:
        folder = spec.parent.name
        rel = spec.relative_to(AGENTS_DIR.parent)
        try:
            doc = yaml.safe_load(spec.read_text())
        except yaml.YAMLError as exc:
            errors.append(f"{rel}: invalid YAML: {exc}")
            continue
        if not isinstance(doc, dict):
            errors.append(f"{rel}: top level must be a mapping")
            continue

        for field in REQUIRED:
            if field not in doc or doc[field] in (None, ""):
                errors.append(f"{rel}: missing required field '{field}'")

        name = doc.get("name")
        if isinstance(name, str):
            if not NAME_RE.match(name):
                errors.append(f"{rel}: name '{name}' must match ^[a-z0-9_-]+$")
            if name != folder:
                errors.append(
                    f"{rel}: name '{name}' must match its folder '{folder}'"
                )
            if name in seen:
                errors.append(
                    f"{rel}: duplicate name '{name}' (also in {seen[name]})"
                )
            else:
                seen[name] = str(rel)

    if errors:
        print("Agent validation failed:\n")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"OK: {len(specs)} agent(s) valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
