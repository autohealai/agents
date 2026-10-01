#!/usr/bin/env python3
"""Validate every agents/<name>/agent.yaml in the repo.

Keeps the contribution bar low but the repo safe: valid YAML, required fields
present, name well-formed, name matches its folder, and names unique. The
optional `metadata` block (which powers the catalog + gallery) is validated when
present. Exits non-zero on any error so CI blocks the PR; warnings are printed
but do not fail the build.
"""
import re
import sys
from pathlib import Path

import yaml

NAME_RE = re.compile(r"^[a-z0-9_-]+$")
REQUIRED = ["schema_version", "name", "description", "instructions"]
AGENTS_DIR = Path(__file__).resolve().parent.parent / "agents"

# Closed sets — an invalid value is an error (it would break the gallery).
CATEGORIES = {"sre", "security", "ci-cd", "cost", "code-review"}
TRIGGERS = {"manual", "schedule"}
# read-only = reads only; notify = posts messages/comments (Slack, PR/issue
# comments), nothing structural; propose = opens PRs and/or issues for a human
# to review (never merges, deploys, or force-pushes).
SAFETY = {"read-only", "notify", "propose"}

# Known integration type slugs (from the product's integrations store). This set
# grows over time, so an unknown slug is a warning, not an error.
KNOWN_INTEGRATIONS = {
    "aws", "azure", "azuredevops", "bigquery", "bitbucket", "chronosphere",
    "clickhouse", "cloudflare", "confluence", "coralogix", "custommcp",
    "customsource", "databricks", "datadog", "drata", "dynatrace",
    "elasticsearch", "featurebase", "fullstory", "gcp", "github", "gitlab",
    "grafana", "honeycomb", "jenkins", "jira", "jsm", "launchdarkly", "mssql",
    "neo4j", "notion", "opensearch", "pagerduty", "postgresql", "posthog",
    "prometheus", "pumble", "pylon", "readmedocs", "recallai", "rivermuse",
    "sentry", "slack", "temporal",
}


def validate_metadata(rel, meta, errors, warnings):
    """Validate the optional metadata block. Missing is a warning; present-but-
    invalid is an error for the closed enums, a warning for integration slugs."""
    if not isinstance(meta, dict):
        errors.append(f"{rel}: 'metadata' must be a mapping")
        return

    category = meta.get("category")
    if category is None:
        warnings.append(f"{rel}: metadata.category missing")
    elif category not in CATEGORIES:
        errors.append(
            f"{rel}: metadata.category '{category}' must be one of "
            f"{sorted(CATEGORIES)}"
        )

    summary = meta.get("summary")
    if not summary:
        warnings.append(f"{rel}: metadata.summary missing (card falls back to description)")
    elif not isinstance(summary, str):
        errors.append(f"{rel}: metadata.summary must be a string")

    trigger = meta.get("trigger")
    if trigger is None:
        warnings.append(f"{rel}: metadata.trigger missing")
    elif trigger not in TRIGGERS:
        errors.append(
            f"{rel}: metadata.trigger '{trigger}' must be one of {sorted(TRIGGERS)}"
        )

    safety = meta.get("safety")
    if safety is None:
        warnings.append(f"{rel}: metadata.safety missing")
    elif safety not in SAFETY:
        errors.append(
            f"{rel}: metadata.safety '{safety}' must be one of {sorted(SAFETY)}"
        )

    requires = meta.get("requires")
    if requires is not None:
        if not isinstance(requires, dict):
            errors.append(f"{rel}: metadata.requires must be a mapping")
        else:
            integrations = requires.get("integrations", [])
            if not isinstance(integrations, list):
                errors.append(f"{rel}: metadata.requires.integrations must be a list")
            else:
                for slug in integrations:
                    if slug not in KNOWN_INTEGRATIONS:
                        warnings.append(
                            f"{rel}: metadata.requires.integrations has unknown "
                            f"slug '{slug}' (typo, or a new integration?)"
                        )


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
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

        if "metadata" in doc:
            validate_metadata(rel, doc["metadata"], errors, warnings)
        else:
            warnings.append(
                f"{rel}: no 'metadata' block — recommended so the agent shows "
                f"richly in the catalog/gallery"
            )

    if warnings:
        print("Warnings (non-blocking):\n")
        for warn in warnings:
            print(f"  - {warn}")
        print()

    if errors:
        print("Agent validation failed:\n")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"OK: {len(specs)} agent(s) valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
