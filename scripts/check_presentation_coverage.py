#!/usr/bin/env python3
"""Check presentation coverage, labels, and live SQL proof discipline.

Enforces reporting-coverage-requirements.md for Matplotlib presentation projects.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


CATALOG_NAMES = (
    "measure_catalog.md",
    "metric_catalog.md",
    "kpi_catalog.md",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def catalog_item_count(path: Path) -> int:
    if not path.exists():
        return 0
    text = read_text(path)
    # Count markdown table data rows after a header separator
    rows = 0
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|\s*-+", stripped):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not cells:
            continue
        first = cells[0].lower()
        if first in {"name", "measure", "metric", "kpi", "id", "measure name", "metric name"}:
            continue
        if first in {"", "---", "none"}:
            continue
        rows += 1
    return rows


def coverage_has_status_rows(path: Path) -> tuple[int, int, int, int]:
    if not path.exists():
        return 0, 0, 0, 0
    text = read_text(path).upper()
    rendered = len(re.findall(r"\bRENDERED\b", text))
    trusted = len(re.findall(r"\bTRUSTED\b", text))
    blocked = len(re.findall(r"\bBLOCKED\b", text))
    deferred = len(re.findall(r"\bDEFERRED\b", text))
    return rendered + trusted, blocked, deferred, trusted


def label_dictionary_maps_categories(path: Path) -> bool:
    if not path.exists():
        return False
    lower = read_text(path).lower()
    return any(token in lower for token in ("expired", "delivered", "partner", "jarir", "status", "tos"))


def sql_verification_executed(sql_dir: Path) -> tuple[int, int]:
    if not sql_dir.exists():
        return 0, 0
    total = 0
    with_result = 0
    for path in sorted(sql_dir.glob("*.sql")):
        total += 1
        text = read_text(path).lower()
        if "captured result" in text or "actual result" in text or "status: pass" in text or "status | pass" in text:
            with_result += 1
    return total, with_result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--min-measures",
        type=int,
        default=50,
        help="Warn when measure_catalog supported-looking rows are below this and coverage is thin.",
    )
    args = parser.parse_args()
    root = args.root.resolve()

    errors: list[str] = []
    warnings: list[str] = []

    insights = root / "reports" / "agent" / "09_analytics_insights"
    kpis = insights / "kpis"
    presentation = root / "reports" / "agent" / "10_presentation" / "matplotlib"

    if not presentation.exists():
        print("SKIPPED: no Matplotlib presentation folder found")
        return 0

    coverage = presentation / "kpi_figure_coverage.md"
    label_dict = presentation / "label_dictionary.md"
    sql_dir = presentation / "sql_verification"
    presentation_report = root / "reports" / "agent" / "10_presentation" / "presentation_report.md"

    if not coverage.exists():
        errors.append("missing reports/agent/10_presentation/matplotlib/kpi_figure_coverage.md")
    if not label_dict.exists():
        errors.append("missing reports/agent/10_presentation/matplotlib/label_dictionary.md")
    else:
        label_text = read_text(label_dict).strip()
        if len(label_text) < 40:
            errors.append("label_dictionary.md exists but is too short to map chart labels")

    measure_count = catalog_item_count(kpis / "measure_catalog.md")
    metric_count = catalog_item_count(kpis / "metric_catalog.md")
    kpi_count = catalog_item_count(kpis / "kpi_catalog.md")
    rendered, blocked, deferred, _trusted_legacy = coverage_has_status_rows(coverage) if coverage.exists() else (0, 0, 0, 0)
    coverage_total = rendered + blocked + deferred

    fact_catalog = insights / "fact_catalog.md"
    gold_facts = 0
    if fact_catalog.exists():
        for line in read_text(fact_catalog).splitlines():
            stripped = line.strip()
            if not stripped.startswith("|") or re.match(r"^\|\s*-+", stripped):
                continue
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if cells and (cells[0].lower().startswith("fct_") or cells[0].lower().startswith("mart_")):
                gold_facts += 1

    if measure_count < args.min_measures:
        msg = (
            f"measure_catalog.md has ~{measure_count} table rows; target is {args.min_measures}+ when gold supports it "
            "(see reporting-coverage-requirements.md / check_analytics_coverage.py)"
        )
        if gold_facts >= 3:
            errors.append(msg)
        else:
            warnings.append(msg)
    if metric_count < 30:
        msg = f"metric_catalog.md has ~{metric_count} table rows; target is 30+ when gold supports it"
        if gold_facts >= 3:
            errors.append(msg)
        else:
            warnings.append(msg)

    catalog_rows = measure_count + metric_count + kpi_count
    if catalog_rows > 0 and coverage_total < max(catalog_rows * 0.5, kpi_count if kpi_count else 1):
        errors.append(
            "kpi_figure_coverage.md does not appear to cover most measure/metric/kpi catalog rows "
            f"(catalog~{catalog_rows}, coverage status tokens={coverage_total})"
        )

    if rendered == 0 and coverage.exists():
        errors.append(
            "kpi_figure_coverage.md has no RENDERED/TRUSTED rows; mark each catalog item RENDERED, BLOCKED, or DEFERRED"
        )

    if label_dict.exists() and not label_dictionary_maps_categories(label_dict):
        warnings.append(
            "label_dictionary.md should map status/partner/category codes to business labels for chart axes"
        )

    sql_total, sql_with_result = sql_verification_executed(sql_dir)
    if rendered > 0 and sql_total == 0:
        errors.append("RENDERED/TRUSTED charts exist but sql_verification/ has no SQL proof files")
    if rendered > 0 and sql_with_result == 0:
        errors.append(
            "RENDERED charts need executed live SQL proofs with captured results in sql_verification/ "
            "(file presence alone is not enough)"
        )
    if rendered > sql_with_result and sql_with_result > 0:
        warnings.append(
            f"RENDERED={rendered} but only {sql_with_result}/{sql_total} sql_verification files show captured results"
        )

    if presentation_report.exists():
        report_text = read_text(presentation_report).lower()
        if "live sql" not in report_text and "sql verification" not in report_text and "refresh" not in report_text:
            warnings.append(
                "presentation_report.md should record live SQL / refresh validation evidence"
            )
    else:
        warnings.append("missing reports/agent/10_presentation/presentation_report.md")

    # Soft check for blank-label language in report assets
    for name in ("report_spec.md", "README.md"):
        path = presentation / name
        if path.exists() and "blank" in read_text(path).lower() and "label" in read_text(path).lower():
            warnings.append(f"{name} mentions blank labels — confirm categorical axes are labeled")

    print(
        f"Catalogs: measures~{measure_count}, metrics~{metric_count}, kpis~{kpi_count}; "
        f"coverage RENDERED/TRUSTED={rendered} BLOCKED={blocked} DEFERRED={deferred}; "
        f"sql_verification={sql_with_result}/{sql_total} with captured results"
    )

    for item in warnings:
        print(f"WARN: {item}")
    for item in errors:
        print(f"ERROR: {item}")

    if errors:
        print("Presentation coverage check FAILED")
        return 1
    if warnings:
        print("Presentation coverage check PASSED with warnings")
        return 0
    print("Presentation coverage check PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
