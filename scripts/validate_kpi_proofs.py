#!/usr/bin/env python3
"""Validate analytics insight KPI catalogs, proof files, and coverage minimums."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lib_gate_common import (
    catalog_item_count,
    cell,
    print_results,
    resolve_proof_path,
    table_dicts,
    validate_sql_proof_file,
)

KPI_DIR = "reports/agent/09_analytics_insights/kpis"
INSIGHTS_DIR = "reports/agent/09_analytics_insights"

ALWAYS_REQUIRED = (
    "reports/agent/KPI_DEFINITION_CONTRACTS.md",
    "reports/agent/METRIC_VERIFICATION_MATRIX.md",
    f"{INSIGHTS_DIR}/business_process_catalog.md",
    f"{INSIGHTS_DIR}/fact_catalog.md",
)

MEASURE_CATALOGS = (
    f"{KPI_DIR}/business_measure_catalog.md",
    f"{KPI_DIR}/measure_catalog.md",
)

METRIC_CATALOGS = (
    f"{KPI_DIR}/business_metric_catalog.md",
    f"{KPI_DIR}/metric_catalog.md",
)

SPECIALIZED_METRIC_CATALOGS = (
    f"{KPI_DIR}/data_quality_metric_catalog.md",
    f"{KPI_DIR}/pipeline_health_metric_catalog.md",
)

KPI_CATALOG = f"{KPI_DIR}/kpi_catalog.md"

OPTIONAL_CATALOGS = (
    f"{KPI_DIR}/kpi_discovery_matrix.md",
    f"{INSIGHTS_DIR}/insight_backlog.md",
    f"{INSIGHTS_DIR}/dimension_catalog.md",
)

LEGACY_CATALOGS = {
    f"{KPI_DIR}/measure_catalog.md": "reports/agent/measure_catalog.md",
    f"{KPI_DIR}/metric_catalog.md": "reports/agent/metric_catalog.md",
    f"{KPI_DIR}/kpi_catalog.md": "reports/agent/kpi_catalog.md",
    f"{KPI_DIR}/kpi_discovery_matrix.md": "reports/agent/kpi_discovery_matrix.md",
    f"{INSIGHTS_DIR}/insight_backlog.md": "reports/agent/insight_backlog.md",
}

SQL_PROOF_DIRS = (
    "reports/agent/09_analytics_insights/kpis/sql_proofs",
    "reports/agent/sql_proofs",
)

PROOF_COLUMNS = (
    "sql_proof",
    "sql proof",
    "proof",
    "proof_file",
    "proof path",
    "source_proof",
    "source proof",
)


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


def resolve_first_existing(root: Path, relatives: tuple[str, ...]) -> Path | None:
    for relative in relatives:
        path = resolve_path(root, relative)
        if path is not None:
            return path
    return None


def resolve_sql_proof_dir(root: Path) -> Path | None:
    for relative in SQL_PROOF_DIRS:
        path = root / relative
        if path.exists() and path.is_dir():
            return path
    return None


def proof_refs_from_catalog(path: Path) -> list[str]:
    refs: list[str] = []
    for row in table_dicts(path):
        for alias in PROOF_COLUMNS:
            ref = cell(row, alias)
            if ref and not ref.lower().startswith(("n/a", "na", "none", "blocked", "deferred")):
                refs.append(ref.strip().strip("`"))
    return refs


def count_catalog_rows(paths: tuple[Path, ...]) -> int:
    total = 0
    for path in paths:
        total += catalog_item_count(path)
    return total


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

    insights = root / "reports" / "agent" / "09_analytics_insights"
    if not insights.exists():
        print("SKIPPED: no analytics insight folder")
        return 0

    errors: list[str] = []
    warnings: list[str] = []

    for relative in ALWAYS_REQUIRED:
        if resolve_path(root, relative) is None:
            errors.append(f"Missing required catalog: {relative}")

    measure_path = resolve_first_existing(root, MEASURE_CATALOGS)
    if measure_path is None:
        errors.append(
            "Missing measure catalog: require business_measure_catalog.md or measure_catalog.md"
        )

    metric_path = resolve_first_existing(root, METRIC_CATALOGS)
    specialized_metric_paths = [
        path
        for relative in SPECIALIZED_METRIC_CATALOGS
        if (path := resolve_path(root, relative)) is not None
    ]
    if metric_path is None and not specialized_metric_paths:
        errors.append(
            "Missing metric catalog: require business_metric_catalog.md, metric_catalog.md, "
            "or at least one specialized data_quality/pipeline_health catalog"
        )

    kpi_path = resolve_path(root, KPI_CATALOG)
    if kpi_path is None:
        errors.append(f"Missing required catalog: {KPI_CATALOG}")

    optional_present = [relative for relative in OPTIONAL_CATALOGS if resolve_path(root, relative)]
    if optional_present:
        print(
            "Optional catalogs present: "
            + ", ".join(Path(item).name for item in optional_present)
        )

    measure_paths = tuple(p for p in (measure_path,) if p)
    metric_path_list: list[Path] = []
    if metric_path is not None:
        metric_path_list.append(metric_path)
    metric_path_list.extend(specialized_metric_paths)
    metric_paths = tuple(metric_path_list)
    kpi_paths = tuple(p for p in (kpi_path,) if p)

    measure_count = count_catalog_rows(measure_paths)
    metric_count = count_catalog_rows(metric_paths)
    kpi_count = count_catalog_rows(kpi_paths)

    if args.min_measures and measure_count < args.min_measures:
        errors.append(
            f"measure catalogs have {measure_count} rows; minimum required is {args.min_measures}"
        )
    if args.min_metrics and metric_count < args.min_metrics:
        errors.append(
            f"metric catalogs have {metric_count} rows; minimum required is {args.min_metrics}"
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

    catalog_paths = [*measure_paths, *metric_paths, *kpi_paths, *specialized_metric_paths]
    referenced_proofs: set[str] = set()
    proof_validation_errors: list[str] = []
    for catalog in catalog_paths:
        for ref in proof_refs_from_catalog(catalog):
            referenced_proofs.add(ref.replace("\\", "/"))
            validation = validate_sql_proof_file(root, ref)
            if validation["errors"]:
                proof_validation_errors.append(
                    f"{catalog.relative_to(root)} -> {ref}: "
                    + "; ".join(validation["errors"][:3])
                )
            elif validation["status"] in {"FAIL", "UNKNOWN"}:
                proof_validation_errors.append(
                    f"{catalog.relative_to(root)} -> {ref}: proof status {validation['status']}"
                )

    if proof_files and catalog_paths and not referenced_proofs:
        warnings.append("Catalogs do not reference sql_proofs/*.sql paths explicitly")

    missing_on_disk: list[str] = []
    for ref in sorted(referenced_proofs):
        if resolve_proof_path(root, ref) is None:
            missing_on_disk.append(ref)

    if missing_on_disk:
        errors.append(
            "Catalog references missing proof files: " + ", ".join(missing_on_disk[:10])
        )
    if proof_validation_errors:
        errors.extend(proof_validation_errors[:20])

    print("KPI proof validation summary:")
    print(f"  measures: {measure_count}")
    print(f"  metrics: {metric_count}")
    print(f"  kpis: {kpi_count}")
    print(f"  sql proof files: {len(proof_files)}")
    print(f"  referenced proofs: {len(referenced_proofs)}")

    return print_results("KPI proof validation", errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
