#!/usr/bin/env python3
"""Check presentation coverage for business pages, proofs, and readability.

Completion is evidence-based — not fixed catalog or card counts.
Exact RENDERED item mapping to _proof_index and sql_verification proof files.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from lib_gate_common import (
    add_output_json_arg,
    catalog_item_count,
    cell,
    count_gold_facts,
    load_analytics_policy,
    print_results,
    read_text,
    ratio,
    table_dicts,
    validate_sql_proof_file,
)


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


def normalize_item_id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_output_json_arg(parser)
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
    proof_required = float(policy.get("rendered_proof_coverage_required", 1.0))
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
    proof_index = sql_dir / "_proof_index.md"
    page_contracts = root / "reports" / "agent" / "10_presentation" / "report_page_contracts.md"

    if not coverage.exists():
        errors.append("missing reports/agent/10_presentation/matplotlib/kpi_figure_coverage.md")
    if not label_dict.exists():
        errors.append("missing reports/agent/10_presentation/matplotlib/label_dictionary.md")
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
    gold_facts = count_gold_facts(root)

    rendered_rows = []
    if coverage.exists():
        for row in table_dicts(coverage, required_any_headers=("item", "status")):
            status = cell(row, "status").upper()
            if status in {"RENDERED", "TRUSTED"}:
                rendered_rows.append(row)

    print(
        f"Presentation coverage: measures~{measure_count}, metrics~{metric_count}, kpis~{kpi_count}; "
        f"RENDERED/TRUSTED={len(rendered_rows)}; gold_facts~{gold_facts}"
    )

    if coverage.exists() and not rendered_rows:
        errors.append("kpi_figure_coverage.md has no RENDERED/TRUSTED rows")

    index_by_item: dict[str, str] = {}
    index_rows = table_dicts(proof_index, required_any_headers=("item", "proof")) if proof_index.exists() else []
    for row in index_rows:
        item = cell(row, "item", "name", "measure", "metric", "kpi")
        proof = cell(row, "proof", "sql_proof", "proof_path", "file")
        if item and proof:
            key = normalize_item_id(item)
            if key in index_by_item:
                errors.append(f"_proof_index.md duplicate item: {item}")
            index_by_item[key] = proof

    proof_complete = 0
    seen_items: set[str] = set()
    for row in rendered_rows:
        item = cell(row, "item", "name", "measure", "metric", "kpi")
        if not item:
            errors.append("kpi_figure_coverage.md RENDERED row missing Item")
            continue
        key = normalize_item_id(item)
        if key in seen_items:
            errors.append(f"kpi_figure_coverage.md duplicate RENDERED item: {item}")
        seen_items.add(key)

        coverage_proof = cell(row, "proof", "sql_proof", "proof_path")
        index_proof = index_by_item.get(key)
        if not index_proof:
            errors.append(f"RENDERED item {item}: missing from _proof_index.md")
            continue
        if coverage_proof and normalize_item_id(coverage_proof) != normalize_item_id(index_proof):
            if Path(coverage_proof).name != Path(index_proof).name:
                warnings.append(
                    f"RENDERED item {item}: coverage proof {coverage_proof} differs from index {index_proof}"
                )

        proof_ref = index_proof if not coverage_proof else coverage_proof
        if not str(proof_ref).startswith("sql_verification"):
            proof_ref = f"sql_verification/{Path(proof_ref).name}"

        result = validate_sql_proof_file(root, f"reports/agent/10_presentation/matplotlib/{proof_ref}")
        if result.get("errors"):
            errors.append(f"RENDERED item {item}: {'; '.join(result['errors'])}")
        else:
            proof_complete += 1

    if rendered_rows and not proof_index.exists():
        errors.append("missing sql_verification/_proof_index.md for RENDERED items")

    cov = ratio(proof_complete, len(rendered_rows))
    if rendered_rows and cov is not None:
        print(f"Rendered proof coverage: {proof_complete}/{len(rendered_rows)} ({cov:.0%})")
        if cov < proof_required:
            errors.append(
                f"rendered proof coverage {cov:.0%} below required {proof_required:.0%}"
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
            '"dimensions"',
            "dimensions",
            'data-tab="dimensions"',
            'data-tab="all_dimensions"',
            'id="dimensions"',
            'id="all_dimensions"',
            "dimension_board",
            "dim_preview",
        )
    )

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
                "measure/metric boards lack display_name/formatted_value — show business titles, not snake_case SQL ids"
            )
        if not has_formatter:
            errors.append(
                "presentation code has no value formatting helper — rates as %, amounts with units/separators"
            )

    dq_catalog = insights / "kpis" / "data_quality_metric_catalog.md"
    pipeline_catalog = insights / "kpis" / "pipeline_health_metric_catalog.md"
    has_dq_metrics = dq_catalog.exists() and len(read_text(dq_catalog).strip()) > 40
    has_pipeline_metrics = pipeline_catalog.exists() and len(read_text(pipeline_catalog).strip()) > 40

    if (gold_facts >= 1 or has_dq_metrics) and not has_dq_page:
        errors.append("Exceptions/Data Quality page required when gold facts or DQ metric catalog exist")
    if (gold_facts >= 1 or has_pipeline_metrics) and not has_pipeline_page:
        errors.append("Pipeline Health page required when gold facts or pipeline-health metric catalog exist")

    gold_sql = list((root / "models" / "gold").rglob("dim_*.sql")) if (root / "models" / "gold").exists() else []
    # Prefer classification/manifest unique_id dimension discovery over filename helpers alone
    from lib_gate_common import list_gold_dimension_names

    classified_dims = list_gold_dimension_names(root)
    if (classified_dims or gold_sql) and not has_dim_tab:
        errors.append(
            "classified/gold dimensions exist but no Dimensions browse tab found "
            "(detection prefers classification unique_id over dim_* filename helpers)"
        )

    if advisory_measures and measure_count < int(advisory_measures) and gold_facts >= 3:
        warnings.append(
            f"advisory: measure_catalog ~{measure_count} below configured advisory_measure_target={advisory_measures}"
        )
    if advisory_metrics and metric_count < int(advisory_metrics) and gold_facts >= 3:
        warnings.append(
            f"advisory: metric_catalog ~{metric_count} below configured advisory_metric_target={advisory_metrics}"
        )

    presentation_report = root / "reports" / "agent" / "10_presentation" / "presentation_report.md"
    if not presentation_report.exists():
        warnings.append("missing reports/agent/10_presentation/presentation_report.md")

    return print_results("Presentation coverage check", errors, warnings, output_json=getattr(args, "output_json", None), validator_id=Path(__file__).stem)


if __name__ == "__main__":
    raise SystemExit(main())
