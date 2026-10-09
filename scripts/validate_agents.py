#!/usr/bin/env python3
"""Validate every agents/<name>/agent.yaml in the repo.

Keeps the contribution bar low but the repo safe: valid YAML, required fields
present, name well-formed, name matches its folder, and names unique. The
optional `metadata` block (which powers the catalog + gallery) is validated when
present. Exits non-zero on any error so CI blocks the PR; warnings are printed
but do not fail the build.

Two formats are accepted:
- `schema_version: 1`, with catalog fields (`display_name`, `metadata`) inside
  agent.yaml.
- `apiVersion: agents.autoheal.ai/v1`. The platform rejects any key it does not
  define, so catalog fields live beside it in catalog.yaml. Only this format
  has private child agents, at agents/<name>/agents/<child>/agent.yaml; each is
  validated too.
"""
import re
import sys
from pathlib import Path

import yaml

NAME_RE = re.compile(r"^[a-z0-9_-]+$")
REQUIRED = ["schema_version", "name", "description", "instructions"]
AGENTS_DIR = Path(__file__).resolve().parent.parent / "agents"

API_VERSION = "agents.autoheal.ai/v1"
REQUIRED_V1 = ["apiVersion", "name", "description"]
# A v1 document is exactly one of these forms.
BODY_V1 = ["instructions", "instructions_template", "steps", "agent", "tool", "runtime"]
# Keys of the schema_version format that a v1 document must not carry: the
# platform refuses the whole document over any of them.
LEGACY_KEYS = ["schema_version", "display_name", "metadata", "capabilities", "model_settings"]
# Where a v1 agent keeps its catalog fields.
CATALOG_FILE = "catalog.yaml"

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


def load(spec, rel, errors):
    """The parsed document, or None after recording why it is unusable."""
    try:
        doc = yaml.safe_load(spec.read_text())
    except yaml.YAMLError as exc:
        errors.append(f"{rel}: invalid YAML: {exc}")
        return None
    if not isinstance(doc, dict):
        errors.append(f"{rel}: top level must be a mapping")
        return None
    return doc


def check_name(rel, doc, folder, errors):
    name = doc.get("name")
    if isinstance(name, str):
        if not NAME_RE.match(name):
            errors.append(f"{rel}: name '{name}' must match ^[a-z0-9_-]+$")
        if name != folder:
            errors.append(f"{rel}: name '{name}' must match its folder '{folder}'")


def validate_v1(rel, doc, errors):
    """The checks the platform would fail a pasted v1 document on first."""
    if doc.get("apiVersion") != API_VERSION:
        errors.append(f"{rel}: apiVersion must be '{API_VERSION}'")
    for field in REQUIRED_V1:
        if field not in doc or doc[field] in (None, ""):
            errors.append(f"{rel}: missing required field '{field}'")
    if not any(key in doc for key in BODY_V1):
        errors.append(f"{rel}: needs one of {BODY_V1}")
    for key in LEGACY_KEYS:
        if key in doc:
            errors.append(
                f"{rel}: '{key}' is not an {API_VERSION} field and the platform "
                f"rejects the document; catalog fields go in {CATALOG_FILE}"
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
        doc = load(spec, rel, errors)
        if doc is None:
            continue

        v1 = "apiVersion" in doc
        if v1:
            validate_v1(rel, doc, errors)
        else:
            for field in REQUIRED:
                if field not in doc or doc[field] in (None, ""):
                    errors.append(f"{rel}: missing required field '{field}'")

        check_name(rel, doc, folder, errors)
        name = doc.get("name")
        if isinstance(name, str):
            if name in seen:
                errors.append(
                    f"{rel}: duplicate name '{name}' (also in {seen[name]})"
                )
            else:
                seen[name] = str(rel)

        if v1:
            catalog = spec.parent / CATALOG_FILE
            if catalog.exists():
                meta = load(catalog, catalog.relative_to(AGENTS_DIR.parent), errors)
                if meta is not None:
                    validate_metadata(rel, meta, errors, warnings)
            else:
                warnings.append(
                    f"{rel}: no {CATALOG_FILE} beside it — recommended so the "
                    f"agent shows richly in the catalog/gallery"
                )
            # Private children: agents/<name>/agents/<child>/agent.yaml.
            for child in sorted(spec.parent.glob("agents/**/agent.yaml")):
                child_rel = child.relative_to(AGENTS_DIR.parent)
                child_doc = load(child, child_rel, errors)
                if child_doc is not None:
                    validate_v1(child_rel, child_doc, errors)
                    check_name(child_rel, child_doc, child.parent.name, errors)
        elif "metadata" in doc:
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
