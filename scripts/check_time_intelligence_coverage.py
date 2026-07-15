#!/usr/bin/env python3
"""Check time-intelligence coverage for published metrics/KPIs."""

from __future__ import annotations

import argparse
from pathlib import Path

from lib_gate_common import (
    cell,
    load_analytics_policy,
    named_status,
    normalize_header,
    print_results,
    ratio,
    table_dicts,
)

PUBLISHED_APPROVALS = {"APPROVED", "PROPOSED"}


def published_metric_ids(root: Path) -> set[str]:
    """Return canonical metric_id / kpi_id obligations only (not display names)."""
    ids: set[str] = set()

    contracts = root / "reports" / "agent" / "KPI_DEFINITION_CONTRACTS.md"
    for row in table_dicts(contracts, required_any_headers=("kpi_id", "approval")):
        approval = cell(row, "approval", "approval_status").upper()
        if approval in PUBLISHED_APPROVALS:
            for alias in ("kpi_id", "kpi", "id"):
                value = cell(row, alias)
                if value:
                    ids.add(normalize_header(value))
                    ids.add(value.strip())

    insights = root / "reports" / "agent" / "09_analytics_insights" / "kpis"
    for catalog_name in ("kpi_catalog.md", "business_metric_catalog.md"):
        catalog = insights / catalog_name
        for row in table_dicts(catalog, required_any_headers=("kpi", "metric", "metric_id")):
            for alias in ("kpi", "kpi_id", "metric", "metric_id"):
                value = cell(row, alias)
                if value:
                    ids.add(normalize_header(value))
                    ids.add(value.strip())

    return {token for token in ids if token}


def coverage_metric_id(row: dict[str, str]) -> str:
    """Primary match key is metric_id; display names are attributes only."""
    return cell(row, "metric_id", "metric id", "kpi_id", "kpi", "metric").strip()


def coverage_display_name(row: dict[str, str]) -> str:
    return cell(row, "display_name", "display name", "metric_name", "metric name").strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    policy = load_analytics_policy(root)
    required = float(policy.get("time_intelligence_coverage_required", 0.8))

    insights = root / "reports" / "agent" / "09_analytics_insights"
    coverage = insights / "time_intelligence_coverage.md"
    contracts = root / "reports" / "agent" / "KPI_DEFINITION_CONTRACTS.md"

    if not insights.exists():
        print("SKIPPED: no analytics insight folder")
        return 0

    metric_ids = published_metric_ids(root)
    if not metric_ids and not contracts.exists():
        print("SKIPPED: no published metrics or KPI contracts yet")
        return 0

    errors: list[str] = []
    warnings: list[str] = []

    if not coverage.exists():
        errors.append(
            "missing time_intelligence_coverage.md — evaluate current/prior/trend support per important metric"
        )
        return print_results("Time intelligence coverage check", errors, warnings)

    rows = table_dicts(
        coverage,
        required_any_headers=("metric", "metric_id", "status", "metric / kpi"),
    )
    covered_ids: set[str] = set()
    supported = 0
    applicable = 0

    for row in rows:
        metric = coverage_metric_id(row)
        display = coverage_display_name(row)
        if not metric:
            if display:
                warnings.append(
                    f"time intelligence row '{display}' missing metric_id — display names are not obligations"
                )
            continue
        covered_ids.add(normalize_header(metric))
        covered_ids.add(metric)
        status = named_status(row)
        if status == "NOT_APPLICABLE":
            continue
        applicable += 1
        if status == "PASS":
            supported += 1
        elif status == "UNKNOWN":
            warnings.append(f"time intelligence row for {metric} has unclear status")

    missing = sorted(
        mid
        for mid in metric_ids
        if normalize_header(mid) not in covered_ids and mid not in covered_ids
    )
    if missing:
        errors.append(
            f"time_intelligence_coverage.md missing published metric IDs: {', '.join(missing[:12])}"
        )

    if applicable == 0 and metric_ids:
        errors.append(
            "time_intelligence_coverage.md has no applicable rows for published metrics"
        )
    else:
        cov = ratio(supported, applicable if applicable else len(metric_ids))
        if cov is None:
            errors.append("time_intelligence_coverage.md has no applicable rows")
        else:
            print(f"Time intelligence coverage: supported={supported}, applicable={applicable} ({cov:.0%})")
            if cov < required:
                errors.append(
                    f"applicable time-intelligence coverage {cov:.0%} below required {required:.0%}"
                )

    return print_results("Time intelligence coverage check", errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
