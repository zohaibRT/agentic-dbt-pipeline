#!/usr/bin/env python3
"""Validate analytics insight KPI catalogs, proof files, and coverage minimums."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_CATALOGS = (
    "reports/agent/09_analytics_insights/kpis/measure_catalog.md",
    "reports/agent/09_analytics_insights/kpis/metric_catalog.md",
    "reports/agent/09_analytics_insights/kpis/kpi_catalog.md",
    "reports/agent/09_analytics_insights/kpis/kpi_discovery_matrix.md",
    "reports/agent/09_analytics_insights/insight_backlog.md",
    "reports/agent/09_analytics_insights/business_process_catalog.md",
    "reports/agent/09_analytics_insights/fact_catalog.md",
    "reports/agent/09_analytics_insights/dimension_catalog.md",
)

LEGACY_CATALOGS = {
    "reports/agent/09_analytics_insights/kpis/measure_catalog.md": "reports/agent/measure_catalog.md",
    "reports/agent/09_analytics_insights/kpis/metric_catalog.md": "reports/agent/metric_catalog.md",
    "reports/agent/09_analytics_insights/kpis/kpi_catalog.md": "reports/agent/kpi_catalog.md",
    "reports/agent/09_analytics_insights/kpis/kpi_discovery_matrix.md": "reports/agent/kpi_discovery_matrix.md",
    "reports/agent/09_analytics_insights/insight_backlog.md": "reports/agent/insight_backlog.md",
}

SQL_PROOF_DIRS = (
    "reports/agent/09_analytics_insights/kpis/sql_proofs",
    "reports/agent/sql_proofs",
)

PROOF_FILE_PATTERN = re.compile(r"sql_proofs[\\/][^\s`|)]+\.sql", re.IGNORECASE)
TABLE_ROW_PATTERN = re.compile(r"^\|(?!\s*-+\s*\|).+\|$")


def resolve_path(root: Path, relative: str) -> Path | None:
    canonical = root / relative
    if canonical.exists():
        return canonical
    legacy = LEGACY_CATALOGS.get(relative)
    if legacy:
        legacy_path = root / legacy
        if legacy_path.exists():
            return legacy_path
    return None


def resolve_sql_proof_dir(root: Path) -> Path | None:
    for relative in SQL_PROOF_DIRS:
        path = root / relative
        if path.exists() and path.is_dir():
            return path
    return None


def count_markdown_table_rows(path: Path) -> int:
    rows = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not TABLE_ROW_PATTERN.match(line.strip()):
            continue
        lowered = line.lower()
        if "measure" in lowered and "measure type" in lowered:
            continue
        if "metric" in lowered and "metric type" in lowered:
            continue
        if "key performance indicator" in lowered and "business question" in lowered:
            continue
        if "business area" in lowered and "business process" in lowered:
            continue
        if "insight" in lowered and "reason" in lowered:
            continue
        if re.search(r"\|-+\|", line):
            continue
        rows += 1
    return rows


def extract_proof_refs(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return PROOF_FILE_PATTERN.findall(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."), help="Project or workspace root")
    parser.add_argument("--min-measures", type=int, default=0, help="Minimum measure catalog rows")
    parser.add_argument("--min-metrics", type=int, default=0, help="Minimum metric catalog rows")
    parser.add_argument("--min-kpis", type=int, default=0, help="Minimum approved KPI rows")
    parser.add_argument(
        "--require-sql-proofs",
        action="store_true",
        help="Require at least one .sql file under sql_proofs/",
    )
    args = parser.parse_args()
    root = args.root.resolve()

    errors: list[str] = []
    warnings: list[str] = []

    for relative in REQUIRED_CATALOGS:
        if resolve_path(root, relative) is None:
            errors.append(f"Missing required catalog: {relative}")

    measure_path = resolve_path(root, REQUIRED_CATALOGS[0])
    metric_path = resolve_path(root, REQUIRED_CATALOGS[1])
    kpi_path = resolve_path(root, REQUIRED_CATALOGS[2])

    measure_count = count_markdown_table_rows(measure_path) if measure_path else 0
    metric_count = count_markdown_table_rows(metric_path) if metric_path else 0
    kpi_count = count_markdown_table_rows(kpi_path) if kpi_path else 0

    if args.min_measures and measure_count < args.min_measures:
        errors.append(
            f"measure_catalog.md has {measure_count} rows; minimum required is {args.min_measures}"
        )
    if args.min_metrics and metric_count < args.min_metrics:
        errors.append(
            f"metric_catalog.md has {metric_count} rows; minimum required is {args.min_metrics}"
        )
    if args.min_kpis and kpi_count < args.min_kpis:
        errors.append(f"kpi_catalog.md has {kpi_count} rows; minimum required is {args.min_kpis}")

    proof_dir = resolve_sql_proof_dir(root)
    proof_files: list[Path] = []
    if proof_dir is None:
        if args.require_sql_proofs or args.min_kpis:
            errors.append("Missing sql_proofs directory under analytics insights")
    else:
        proof_files = sorted(proof_dir.glob("*.sql"))
        if args.require_sql_proofs and not proof_files:
            errors.append(f"No .sql proof files found in {proof_dir.relative_to(root)}")

    catalog_paths = [p for p in (measure_path, metric_path, kpi_path) if p]
    referenced_proofs: set[str] = set()
    for catalog in catalog_paths:
        for ref in extract_proof_refs(catalog):
            referenced_proofs.add(ref.replace("\\", "/"))

    if proof_files and catalog_paths and not referenced_proofs:
        warnings.append("Catalogs do not reference sql_proofs/*.sql paths explicitly")

    missing_on_disk: list[str] = []
    for ref in sorted(referenced_proofs):
        candidate = root / ref.replace("/", "\\") if sys.platform == "win32" else root / ref
        if not candidate.exists():
            alt = root / "reports/agent/09_analytics_insights/kpis" / Path(ref).name
            if not alt.exists():
                missing_on_disk.append(ref)

    if missing_on_disk:
        errors.append(
            "Catalog references missing proof files: " + ", ".join(missing_on_disk[:10])
        )

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    print("KPI proof validation summary:")
    print(f"  measures: {measure_count}")
    print(f"  metrics: {metric_count}")
    print(f"  kpis: {kpi_count}")
    print(f"  sql proof files: {len(proof_files)}")

    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("KPI proof validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
