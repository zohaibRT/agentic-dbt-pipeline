#!/usr/bin/env python3
"""Check presentation coverage for business pages, proofs, and readability.

Completion is evidence-based — not fixed 50+/50+ catalog or card counts.
All Measures / All Metrics may exist as dictionary pages but are not required
to hit an arbitrary size. See reporting-coverage-requirements.md Rules 5b–5c
and report-page-contract.md.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from lib_gate_common import (
    catalog_item_count,
    count_gold_facts,
    load_analytics_policy,
    print_results,
    read_text,
)


def coverage_has_status_rows(path: Path) -> tuple[int, int, int]:
    if not path.exists():
        return 0, 0, 0
    text = read_text(path).upper()
    rendered = len(re.findall(r"\bRENDERED\b", text))
    trusted = len(re.findall(r"\bTRUSTED\b", text))
    blocked = len(re.findall(r"\bBLOCKED\b", text))
    deferred = len(re.findall(r"\bDEFERRED\b", text))
    return rendered + trusted, blocked, deferred


def label_dictionary_maps_categories(path: Path) -> bool:
    if not path.exists():
        return False
    text = read_text(path)
    lower = text.lower()
    has_table = bool(re.search(r"^\|.+\|$", text, re.M)) and "---" in text
    has_label_col = any(
        token in lower
        for token in ("business label", "display label", "label", "code", "maps to", "meaning", "description")
    )
    return has_table and has_label_col


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


def collect_builder_text(presentation: Path) -> str:
    return "\n".join(
        read_text(p)
        for p in (
            presentation / "report_builder.py",
            presentation / "data_access.py",
            presentation / "serve_report.py",
            presentation / "report.html",
            presentation / "report_spec.md",
        )
        if p.exists()
    ).lower()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--advisory-measure-target",
        type=int,
        default=None,
        help="Optional advisory catalog size warning only (never hard FAIL by default).",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    policy = load_analytics_policy(root)
    advisory_measures = args.advisory_measure_target
    if advisory_measures is None:
        advisory_measures = policy.get("advisory_measure_target")
    advisory_metrics = policy.get("advisory_metric_target")

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
    page_contracts = root / "reports" / "agent" / "10_presentation" / "report_page_contracts.md"

    if not coverage.exists():
        errors.append("missing reports/agent/10_presentation/matplotlib/kpi_figure_coverage.md")
    if not label_dict.exists():
        errors.append("missing reports/agent/10_presentation/matplotlib/label_dictionary.md")
    else:
        label_text = read_text(label_dict).strip()
        if len(label_text) < 40:
            errors.append("label_dictionary.md exists but is too short to map chart labels")
        elif not label_dictionary_maps_categories(label_dict):
            warnings.append("label_dictionary.md should map codes/keys to business labels for chart axes")

    if not page_contracts.exists():
        warnings.append(
            "missing reports/agent/10_presentation/report_page_contracts.md — "
            "each page should declare audience, purpose, KPIs, period, and actions"
        )

    measure_count = catalog_item_count(kpis / "measure_catalog.md") or catalog_item_count(
        kpis / "business_measure_catalog.md"
    )
    metric_count = catalog_item_count(kpis / "metric_catalog.md") or catalog_item_count(
        kpis / "business_metric_catalog.md"
    )
    kpi_count = catalog_item_count(kpis / "kpi_catalog.md")
    rendered, blocked, deferred = coverage_has_status_rows(coverage) if coverage.exists() else (0, 0, 0)
    coverage_total = rendered + blocked + deferred
    gold_facts = count_gold_facts(root)

    print(
        f"Presentation coverage: measures~{measure_count}, metrics~{metric_count}, kpis~{kpi_count}; "
        f"coverage RENDERED/TRUSTED={rendered} BLOCKED={blocked} DEFERRED={deferred}; gold_facts~{gold_facts}"
    )

    # Advisory counts only — never the default hard gate
    if advisory_measures and measure_count < int(advisory_measures) and gold_facts >= 3:
        warnings.append(
            f"advisory: measure_catalog ~{measure_count} below configured advisory_measure_target={advisory_measures}"
        )
    if advisory_metrics and metric_count < int(advisory_metrics) and gold_facts >= 3:
        warnings.append(
            f"advisory: metric_catalog ~{metric_count} below configured advisory_metric_target={advisory_metrics}"
        )

    if coverage.exists() and coverage_total == 0:
        errors.append(
            "kpi_figure_coverage.md has no RENDERED/BLOCKED/DEFERRED rows; map published report items"
        )
    if coverage.exists() and rendered == 0 and coverage_total > 0:
        warnings.append("kpi_figure_coverage.md has no RENDERED/TRUSTED rows yet")

    # Traceability: published catalogs should mostly appear as coverage rows
    catalog_rows = measure_count + metric_count + kpi_count
    if catalog_rows > 0 and coverage_total > 0:
        # Prefer process coverage over forcing 50% of every catalog row onto a page
        if coverage_total < max(kpi_count, 1) and kpi_count > 0:
            errors.append(
                f"kpi_figure_coverage.md under-covers strategic KPIs (kpis~{kpi_count}, coverage rows~{coverage_total})"
            )
        elif coverage_total < max(int(catalog_rows * 0.25), 1):
            warnings.append(
                f"kpi_figure_coverage.md covers few catalog rows (catalog~{catalog_rows}, coverage~{coverage_total}) — "
                "ensure business pages map published metrics; full raw catalogs may live under Metric Dictionary"
            )

    builder_text = collect_builder_text(presentation)
    has_measure_board = any(
        token in builder_text
        for token in ("all measures", "measure_board", "measure_cards", 'data-tab="measures"', 'id="measures"')
    )
    has_metric_board = any(
        token in builder_text
        for token in ("all metrics", "metric_board", "metric_cards", 'data-tab="metrics"', 'id="metrics"')
    )
    has_dq_page = any(
        token in builder_text
        for token in ("data quality", "exceptions", "observability", 'data-tab="quality"', 'id="quality"')
    )
    has_pipeline_page = any(
        token in builder_text
        for token in ("pipeline health", "pipeline", 'data-tab="pipeline"', 'id="pipeline"')
    )
    has_dim_tab = any(
        token in builder_text
        for token in (
            "all dimensions",
            "dimensions tab",
            'data-tab="dimensions"',
            'id="dimensions"',
            "dimension_board",
            "dim_preview",
        )
    )

    # Boards optional as dictionary pages; if present, must be human-readable
    if has_measure_board or has_metric_board:
        has_display_name = any(
            token in builder_text
            for token in ("display_name", "display name", "formatted_value", "formatted value", "business_label")
        )
        has_formatter = any(
            token in builder_text
            for token in ("format_value", "formatted_value", "format_percent", ":.1%", ":.2%", "currency", "thousands")
        )
        if not has_display_name:
            errors.append(
                "measure/metric boards lack display_name/formatted_value — "
                "show business titles, not snake_case SQL ids (Rule 5c)"
            )
        if not has_formatter:
            errors.append(
                "presentation code has no value formatting helper — "
                "rates as %, amounts with units/separators (Rule 5c)"
            )

    if gold_facts >= 1 and not has_dq_page:
        warnings.append("no Exceptions/Data Quality page markers found in presentation surface")
    if gold_facts >= 1 and not has_pipeline_page:
        warnings.append("no Pipeline Health page markers found in presentation surface")

    gold_sql = list((root / "models" / "gold").rglob("dim_*.sql")) if (root / "models" / "gold").exists() else []
    if gold_sql and not has_dim_tab:
        warnings.append(
            "gold dimensions exist but no Dimensions browse tab found — "
            "prefer readable dim tables over dim_*_row_count as business measures"
        )

    sql_total, sql_with_result = sql_verification_executed(sql_dir)
    proof_index = sql_dir / "_proof_index.md"
    if rendered > 0 and sql_total == 0:
        errors.append("RENDERED/TRUSTED charts exist but sql_verification/ has no SQL proof files")
    if rendered > 0 and sql_with_result == 0:
        errors.append(
            "RENDERED charts need executed live SQL proofs with captured results in sql_verification/"
        )
    if (has_measure_board or has_metric_board) and gold_facts >= 1:
        if not proof_index.exists():
            errors.append(
                "missing sql_verification/_proof_index.md — map RENDERED board/chart items to SQL proofs"
            )
        if sql_with_result < 3:
            errors.append(
                f"boards/charts require executed sql_verification proofs "
                f"(have {sql_with_result} with captured results; need >= 3)"
            )
        index_text = read_text(proof_index).lower() if proof_index.exists() else ""
        if proof_index.exists() and "measure" not in index_text and "metric" not in index_text and "kpi" not in index_text:
            warnings.append("_proof_index.md should map measure/metric/KPI items to proof files")

    if presentation_report.exists():
        report_text = read_text(presentation_report).lower()
        if "live sql" not in report_text and "sql verification" not in report_text and "refresh" not in report_text:
            warnings.append("presentation_report.md should record live SQL / refresh validation evidence")
    else:
        warnings.append("missing reports/agent/10_presentation/presentation_report.md")

    for name in ("report_spec.md", "README.md"):
        path = presentation / name
        if path.exists() and "blank" in read_text(path).lower() and "label" in read_text(path).lower():
            warnings.append(f"{name} mentions blank labels — confirm categorical axes are labeled")

    print(f"sql_verification={sql_with_result}/{sql_total} with captured results")
    return print_results("Presentation coverage check", errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
