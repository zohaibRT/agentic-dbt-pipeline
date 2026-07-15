#!/usr/bin/env python3
"""Evaluate analytics product completeness from process/fact coverage.

Replaces fixed 50+/50+ catalog-row targets with evidence-based coverage:
- analytics_coverage_matrix.md present and populated when insights exist
- separated business vs quality/pipeline catalogs preferred
- per-fact coverage contract evaluated when fact_coverage_contracts.md exists
- thin catalogs still WARN when rich gold has almost no measures

See references/analytics-product-completeness.md.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from lib_gate_common import load_analytics_policy


HEADER_TOKENS = {
    "name",
    "measure",
    "metric",
    "kpi",
    "id",
    "measure name",
    "metric name",
    "business process",
    "facts",
    "fact",
    "dimensions",
    "none",
    "",
    "---",
}


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def catalog_item_count(path: Path) -> int:
    if not path.exists():
        return 0
    rows = 0
    for line in read_text(path).splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|\s*-+", stripped):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not cells:
            continue
        first = cells[0].lower()
        if first in HEADER_TOKENS or first.startswith("<") or first.startswith("kg-"):
            continue
        rows += 1
    return rows


def table_data_rows(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    if not path.exists():
        return rows
    for line in read_text(path).splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|\s*-+", stripped):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not cells:
            continue
        first = cells[0].lower()
        if first in HEADER_TOKENS or first.startswith("<"):
            continue
        rows.append(cells)
    return rows


def count_gold_facts(root: Path) -> int:
    fact_catalog = root / "reports" / "agent" / "09_analytics_insights" / "fact_catalog.md"
    text = read_text(fact_catalog)
    if text:
        count = 0
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.startswith("|") or re.match(r"^\|\s*-+", stripped):
                continue
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if not cells:
                continue
            name = cells[0].lower()
            if name in {"fact model", "model", "name", ""}:
                continue
            if name.startswith("fct_") or name.startswith("mart_"):
                count += 1
        if count:
            return count

    gold = root / "models" / "gold"
    if not gold.exists():
        return 0
    return sum(1 for path in gold.rglob("*.sql") if path.name.startswith(("fct_", "mart_")))


def count_pass_rows(path: Path, status_col_hints: tuple[str, ...] = ("pass", "status")) -> tuple[int, int]:
    """Return (pass_like_rows, total_data_rows) for a markdown matrix."""
    rows = table_data_rows(path)
    if not rows:
        return 0, 0
    pass_rows = 0
    for cells in rows:
        joined = " ".join(cells).lower()
        if "pass" in joined and "blocked" not in joined.split("pass")[-1][:12]:
            pass_rows += 1
        elif any(c.strip().upper() == "PASS" for c in cells):
            pass_rows += 1
    return pass_rows, len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--min-process-coverage",
        type=float,
        default=None,
        help="Minimum fraction of analytics_coverage_matrix rows that should be PASS-like",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    policy = load_analytics_policy(root)
    if args.min_process_coverage is None:
        args.min_process_coverage = float(policy.get("business_process_coverage_required", 0.9))

    insights = root / "reports" / "agent" / "09_analytics_insights"
    if not insights.exists():
        print("SKIPPED: no analytics insight folder")
        return 0

    kpis = insights / "kpis"
    measure_path = kpis / "measure_catalog.md"
    metric_path = kpis / "metric_catalog.md"
    business_measure = kpis / "business_measure_catalog.md"
    business_metric = kpis / "business_metric_catalog.md"
    dq_catalog = kpis / "data_quality_metric_catalog.md"
    pipeline_catalog = kpis / "pipeline_health_metric_catalog.md"
    coverage_matrix = insights / "analytics_coverage_matrix.md"
    fact_contracts = insights / "fact_coverage_contracts.md"

    if not any(p.exists() for p in (measure_path, metric_path, business_measure, business_metric, coverage_matrix)):
        print("SKIPPED: analytics catalogs / coverage matrix not found yet")
        return 0

    gold_facts = count_gold_facts(root)
    measure_count = catalog_item_count(measure_path) or catalog_item_count(business_measure)
    metric_count = catalog_item_count(metric_path) or catalog_item_count(business_metric)
    dq_count = catalog_item_count(dq_catalog)
    pipeline_count = catalog_item_count(pipeline_catalog)
    coverage_pass, coverage_total = count_pass_rows(coverage_matrix)
    fact_pass, fact_total = count_pass_rows(fact_contracts)

    print(
        "Analytics product coverage: "
        f"gold_facts~{gold_facts}, business_measures~{measure_count}, "
        f"business_metrics~{metric_count}, quality_metrics~{dq_count}, "
        f"pipeline_metrics~{pipeline_count}, "
        f"coverage_matrix={coverage_pass}/{coverage_total}, "
        f"fact_contracts={fact_pass}/{fact_total}"
    )

    errors: list[str] = []
    warnings: list[str] = []

    if gold_facts >= 1 and not coverage_matrix.exists():
        errors.append(
            "missing reports/agent/09_analytics_insights/analytics_coverage_matrix.md — "
            "process/fact coverage is the primary gate (not fixed 50+ row counts)"
        )
    elif coverage_total > 0:
        ratio = coverage_pass / coverage_total
        print(f"Business-process coverage: {ratio:.0%} (target >= {args.min_process_coverage:.0%})")
        if ratio < args.min_process_coverage:
            errors.append(
                f"analytics_coverage_matrix.md PASS-like coverage {ratio:.0%} "
                f"is below target {args.min_process_coverage:.0%}"
            )

    if gold_facts >= 1 and not fact_contracts.exists():
        warnings.append(
            "missing fact_coverage_contracts.md — evaluate each fct_/mart_ for volume, value, "
            "status, time, dimensions, quality, reconciliation, and business questions"
        )
    elif fact_total > 0 and fact_pass < fact_total:
        warnings.append(
            f"fact_coverage_contracts.md incomplete: {fact_pass}/{fact_total} PASS-like rows"
        )

    if gold_facts >= 3 and measure_count < 5:
        errors.append(
            f"business/measure catalogs have only ~{measure_count} rows while gold has "
            f"{gold_facts} facts/marts — incomplete analytical coverage for material facts"
        )
    elif gold_facts >= 1 and measure_count == 0:
        warnings.append("no business measures catalogued yet")

    if gold_facts >= 3 and metric_count < 5:
        warnings.append(
            f"business/metric catalogs have only ~{metric_count} rows with {gold_facts} gold facts — "
            "expand rates/shares/trends only where they answer documented business questions"
        )

    if business_measure.exists() or business_metric.exists():
        if measure_path.exists() and metric_path.exists() and dq_count == 0 and pipeline_count == 0:
            warnings.append(
                "prefer separate data_quality_metric_catalog.md and pipeline_health_metric_catalog.md "
                "so technical counts do not mix into business pages"
            )
    elif measure_path.exists() and "row_count" in read_text(measure_path).lower():
        warnings.append(
            "measure_catalog.md appears to mix model row_count / engineering QA with business measures — "
            "split into business_measure_catalog.md and data_quality_metric_catalog.md"
        )

    for item in warnings:
        print(f"WARN: {item}")
    for item in errors:
        print(f"ERROR: {item}")

    if errors:
        print("Analytics coverage check FAILED")
        return 1
    if warnings:
        print("Analytics coverage check PASSED with warnings")
        return 0
    print("Analytics coverage check PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
