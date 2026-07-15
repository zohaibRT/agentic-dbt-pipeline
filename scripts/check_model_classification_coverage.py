#!/usr/bin/env python3
"""Check model classification coverage for in-scope models."""

from __future__ import annotations

import argparse
from pathlib import Path

from lib_gate_common import (
    cell,
    inventory_from_filesystem,
    inventory_from_manifest,
    load_analytics_policy,
    load_manifest,
    print_results,
    ratio,
    table_dicts,
)


def build_inventory(root: Path) -> list[dict]:
    manifest = load_manifest(root)
    if manifest:
        return inventory_from_manifest(manifest)
    return inventory_from_filesystem(root)


def in_scope_models(inventory: list[dict]) -> dict[str, dict]:
    models: dict[str, dict] = {}
    for resource in inventory:
        if resource.get("resource_type") != "model":
            continue
        if resource.get("enabled") is False:
            continue
        name = str(resource.get("name", "")).strip().lower()
        unique_id = str(resource.get("unique_id", "")).strip()
        if name:
            models[name] = resource
        if unique_id:
            models[unique_id] = resource
    return models


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    policy = load_analytics_policy(root)
    required = float(policy.get("model_classification_coverage_required", 1.0))

    insights = root / "reports" / "agent" / "09_analytics_insights"
    classification = insights / "model_classification.md"
    inventory = build_inventory(root)
    model_index = in_scope_models(inventory)
    built_names = {
        str(resource.get("name", "")).strip().lower()
        for resource in inventory
        if resource.get("resource_type") == "model" and resource.get("enabled") is not False
    }
    built_names = {name for name in built_names if name}

    if not insights.exists() and not built_names:
        print("SKIPPED: no analytics insights or models yet")
        return 0
    if not built_names:
        print("SKIPPED: no SQL models under models/")
        return 0

    errors: list[str] = []
    warnings: list[str] = []

    if not classification.exists():
        errors.append("missing reports/agent/09_analytics_insights/model_classification.md")
        return print_results("Model classification coverage check", errors, warnings)

    rows = table_dicts(classification, required_any_headers=("model", "class", "name"))
    if not rows:
        errors.append("model_classification.md has no classification rows")
        return print_results("Model classification coverage check", errors, warnings)

    classified_names: set[str] = set()
    classified_unique_ids: set[str] = set()
    name_only_matches = 0

    for row in rows:
        unique_id = cell(row, "unique_id", "unique id", "node_id", "node id")
        model_name = cell(row, "model", "model_name", "name").lower().replace("`", "")
        class_text = cell(row, "class", "model_class", "classification")
        if not model_name and not unique_id:
            continue
        if unique_id:
            classified_unique_ids.add(unique_id)
            if unique_id in model_index:
                classified_names.add(str(model_index[unique_id].get("name", "")).lower())
        elif model_name:
            classified_names.add(model_name)
            if model_name in built_names:
                name_only_matches += 1
        if not class_text:
            label = unique_id or model_name
            errors.append(f"{label}: classification row missing model class")

    missing = sorted(name for name in built_names if name not in classified_names)
    matched = len(built_names) - len(missing)
    coverage = ratio(matched, len(built_names))
    if coverage is None:
        errors.append("no built models to classify (empty inventory is NOT_APPLICABLE, not 100%)")
    else:
        source = "manifest" if load_manifest(root) else "filesystem"
        print(
            f"Model classification ({source}): classified={matched}/{len(built_names)} ({coverage:.0%})"
        )
        if coverage < required:
            errors.append(
                f"model classification coverage {coverage:.0%} below required {required:.0%}; "
                f"missing examples: {', '.join(missing[:8])}"
            )
        elif missing:
            warnings.append(f"unclassified models remain: {', '.join(missing[:8])}")

    if name_only_matches and not classified_unique_ids:
        warnings.append(
            "model_classification.md uses name-only matching — prefer unique_id when manifest is available"
        )

    return print_results("Model classification coverage check", errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
