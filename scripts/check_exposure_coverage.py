#!/usr/bin/env python3
"""Check downstream exposure coverage documentation."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from lib_gate_common import (
    cell,
    load_analytics_policy,
    load_manifest,
    load_yaml,
    print_results,
    ratio,
    read_text,
    table_dicts,
)

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


def parse_exposure_yaml_files(root: Path) -> list[dict[str, Any]]:
    exposures: list[dict[str, Any]] = []
    models_dir = root / "models"
    if not models_dir.exists():
        return exposures
    for path in sorted(models_dir.rglob("exposures*.yml")):
        data = load_yaml(path)
        for entry in data.get("exposures") or []:
            if isinstance(entry, dict):
                entry = dict(entry)
                entry["_source"] = str(path.relative_to(root))
                exposures.append(entry)
    return exposures


def manifest_exposures(root: Path) -> list[dict[str, Any]]:
    manifest = load_manifest(root)
    if not manifest:
        return []
    nodes = manifest.get("exposures", {})
    results: list[dict[str, Any]] = []
    if isinstance(nodes, dict):
        for node_id, node in nodes.items():
            if isinstance(node, dict):
                row = dict(node)
                row["unique_id"] = node_id
                results.append(row)
    return results


def manifest_node_ids(root: Path) -> set[str]:
    manifest = load_manifest(root)
    if not manifest:
        return set()
    ids: set[str] = set()
    for bucket in ("nodes", "sources", "exposures", "metrics"):
        section = manifest.get(bucket, {})
        if isinstance(section, dict):
            ids.update(section.keys())
    return ids


def exposure_name(entry: dict[str, Any]) -> str:
    return str(entry.get("name") or entry.get("label") or entry.get("unique_id") or "").strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    policy = load_analytics_policy(root)
    required_ratio = float(policy.get("production_exposure_coverage_required", 1.0))

    insights = root / "reports" / "agent" / "09_analytics_insights"
    presentation = root / "reports" / "agent" / "10_presentation"
    coverage_path = insights / "exposure_coverage.md"

    yaml_exposures = parse_exposure_yaml_files(root)
    manifest_rows = manifest_exposures(root)
    known_nodes = manifest_node_ids(root)

    if not insights.exists() and not presentation.exists() and not yaml_exposures and not manifest_rows:
        print("SKIPPED: no analytics/presentation/exposures yet")
        return 0

    errors: list[str] = []
    warnings: list[str] = []

    presentation_exists = presentation.exists()
    if presentation_exists and not coverage_path.exists():
        errors.append(
            "presentation exists but exposure_coverage.md is missing"
        )
        return print_results("Exposure coverage check", errors, warnings)

    documented: set[str] = set()
    complete_docs = 0
    if coverage_path.exists():
        rows = table_dicts(coverage_path, required_any_headers=("exposure", "owner"))
        for row in rows:
            name = cell(row, "exposure", "name", "exposure_name")
            if name:
                documented.add(name.lower())
            owner = cell(row, "owner")
            purpose = cell(row, "business purpose", "business_purpose", "purpose")
            validation = cell(row, "validation status", "validation_status", "status")
            if name and owner and purpose and validation:
                complete_docs += 1
            elif name:
                missing = []
                if not owner:
                    missing.append("owner")
                if not purpose:
                    missing.append("business purpose")
                if not validation:
                    missing.append("validation status")
                errors.append(f"exposure_coverage.md row {name}: missing {', '.join(missing)}")
        print(f"Exposure coverage: rows={len(rows)}, documented={len(documented)}")

    exposure_sources = manifest_rows or [
        {"name": exposure_name(e), "owner": e.get("owner"), "depends_on": e.get("depends_on")}
        for e in yaml_exposures
    ]

    if not exposure_sources and presentation_exists:
        # Presentation-only projects still need documented browser_report style exposure
        presentation_report = presentation / "presentation_report.md"
        matplotlib = presentation / "matplotlib" / "report.html"
        if matplotlib.exists() and "browser_report" not in documented and "browser report" not in documented:
            warnings.append("presentation HTML exists but no browser_report exposure documented")

    validated = 0
    for entry in exposure_sources:
        name = exposure_name(entry)
        if not name:
            continue
        owner = entry.get("owner") or entry.get("meta", {}).get("owner") if isinstance(entry.get("meta"), dict) else entry.get("owner")
        if not owner:
            errors.append(f"exposure {name}: missing owner")
        depends = entry.get("depends_on")
        deps: list[str] = []
        if isinstance(depends, dict):
            deps = list(depends.get("nodes") or [])
        elif isinstance(depends, list):
            deps = [str(item) for item in depends]
        if known_nodes and deps:
            missing_deps = [dep for dep in deps if dep not in known_nodes]
            if missing_deps:
                errors.append(
                    f"exposure {name}: depends_on nodes missing from manifest: {', '.join(missing_deps[:6])}"
                )
        if presentation_exists and name.lower() not in documented:
            errors.append(f"exposure {name}: not documented in exposure_coverage.md")
        else:
            validated += 1

    total = len(exposure_sources) if exposure_sources else (1 if presentation_exists else 0)
    if presentation_exists and total > 0:
        cov = ratio(validated if exposure_sources else complete_docs, total)
        if cov is not None:
            print(f"Production exposure coverage: {validated if exposure_sources else complete_docs}/{total} ({cov:.0%})")
            if cov < required_ratio:
                errors.append(
                    f"production exposure coverage {cov:.0%} below required {required_ratio:.0%}"
                )

    if coverage_path.exists():
        text = read_text(coverage_path).lower()
        for hint in ("owner", "dependent", "business purpose", "criticality", "validation"):
            if hint not in text:
                warnings.append(f"exposure_coverage.md missing hint: {hint}")

    return print_results("Exposure coverage check", errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
