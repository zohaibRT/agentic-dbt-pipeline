#!/usr/bin/env python3
"""Fail analytics when measure/metric catalogs are thin vs available gold.

Enforces reporting-coverage-requirements.md Rule 1 after analytics insight
reporting. Presentation must not proceed as PASS with 10–15 executive measures
when gold has multiple facts and dimensions.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


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
        if first in {
            "name",
            "measure",
            "metric",
            "kpi",
            "id",
            "measure name",
            "metric name",
            "none",
            "",
            "---",
        }:
            continue
        if first.startswith("<") or first.startswith("kg-"):
            continue
        rows += 1
    return rows


def count_gold_facts(root: Path) -> int:
    fact_catalog = root / "reports" / "agent" / "09_analytics_insights" / "fact_catalog.md"
    text = read_text(fact_catalog)
    if text:
        count = 0
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.startswith("|"):
                continue
            if re.match(r"^\|\s*-+", stripped):
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


def shortfall_documented(root: Path) -> bool:
    """Allow WARN-only when analytics explicitly proves gold cannot support the target."""
    text = "\n".join(
        [
            read_text(root / "reports" / "agent" / "09_analytics_insights" / "insight_backlog.md"),
            read_text(root / "reports" / "agent" / "09_analytics_insights" / "analytics_insight_report.md"),
            read_text(root / "reports" / "agent" / "09_analytics_insights" / "analytics_insight_reporting_report.md"),
        ]
    ).lower()
    markers = (
        "cannot reach 50+",
        "cannot reach 50 measures",
        "gold cannot support 50",
        "coverage shortfall accepted",
        "measure target impossible",
        "only n facts",
        "single fact",
    )
    return any(marker in text for marker in markers)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--min-measures", type=int, default=50)
    parser.add_argument("--min-metrics", type=int, default=30)
    parser.add_argument("--min-gold-facts", type=int, default=3)
    args = parser.parse_args()
    root = args.root.resolve()

    insights = root / "reports" / "agent" / "09_analytics_insights"
    if not insights.exists():
        print("SKIPPED: no analytics insight folder")
        return 0

    kpis = insights / "kpis"
    measure_path = kpis / "measure_catalog.md"
    metric_path = kpis / "metric_catalog.md"
    if not measure_path.exists() and not metric_path.exists():
        print("SKIPPED: measure_catalog.md and metric_catalog.md not found yet")
        return 0

    measure_count = catalog_item_count(measure_path)
    metric_count = catalog_item_count(metric_path)
    gold_facts = count_gold_facts(root)

    print(
        f"Analytics coverage: measures~{measure_count} (target {args.min_measures}+), "
        f"metrics~{metric_count} (target {args.min_metrics}+), gold_facts~{gold_facts}"
    )

    errors: list[str] = []
    warnings: list[str] = []

    rich_gold = gold_facts >= args.min_gold_facts
    if rich_gold and measure_count < args.min_measures:
        msg = (
            f"measure_catalog.md has ~{measure_count} rows; target is {args.min_measures}+ "
            f"when gold has {gold_facts} facts/marts. Expand counts/amounts/status/quality "
            "measures from every fct_/mart_ before presentation."
        )
        if shortfall_documented(root):
            warnings.append(msg + " (documented shortfall — WARN only)")
        else:
            errors.append(msg)

    if rich_gold and metric_count < args.min_metrics:
        msg = (
            f"metric_catalog.md has ~{metric_count} rows; target is {args.min_metrics}+ "
            "with ratios, shares, trends, and partner/program/product slices."
        )
        if shortfall_documented(root):
            warnings.append(msg + " (documented shortfall — WARN only)")
        else:
            errors.append(msg)

    if not rich_gold and measure_count < 15:
        warnings.append(
            f"gold_facts~{gold_facts}: still expand measure_catalog beyond thin executive lists when possible"
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
