#!/usr/bin/env python3
"""Evaluate analytics product completeness from process/fact coverage.

Completion is evidence-based — never fixed catalog count quotas.
Uses explicit Status / Verification columns via lib_gate_common helpers.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lib_gate_common import (
    catalog_item_count,
    cell,
    count_gold_facts,
    count_status_rows,
    load_analytics_policy,
    named_status,
    print_results,
    ratio,
    read_text,
    table_dicts,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--min-process-coverage",
        type=float,
        default=None,
        help="Override analytics_policy.business_process_coverage_required",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    policy = load_analytics_policy(root)
    min_process = (
        float(args.min_process_coverage)
        if args.min_process_coverage is not None
        else float(policy.get("business_process_coverage_required", 0.9))
    )
    fact_required = float(policy.get("critical_fact_coverage_required", 1.0))
    recon_required = float(policy.get("critical_reconciliation_coverage_required", 1.0))
    time_required = float(policy.get("time_intelligence_coverage_required", 0.8))
    dq_required = float(policy.get("critical_data_quality_coverage_required", 1.0))
    trace_required = float(policy.get("report_traceability_required", 1.0))

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
    time_cov = insights / "time_intelligence_coverage.md"
    obs_cov = insights / "data_observability_coverage.md"
    figure_cov = root / "reports" / "agent" / "10_presentation" / "matplotlib" / "kpi_figure_coverage.md"

    if not any(
        p.exists()
        for p in (measure_path, metric_path, business_measure, business_metric, coverage_matrix)
    ):
        print("SKIPPED: analytics catalogs / coverage matrix not found yet")
        return 0

    gold_facts = count_gold_facts(root)
    measure_count = catalog_item_count(measure_path) or catalog_item_count(business_measure)
    metric_count = catalog_item_count(metric_path) or catalog_item_count(business_metric)
    dq_count = catalog_item_count(dq_catalog)
    pipeline_count = catalog_item_count(pipeline_catalog)
    coverage_pass, coverage_total, coverage_unknown = count_status_rows(coverage_matrix)
    fact_pass, fact_total, fact_unknown = count_status_rows(fact_contracts)

    print(
        "Analytics product coverage (informational counts only): "
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
            "missing analytics_coverage_matrix.md — process/fact coverage is the primary gate"
        )
    else:
        cov = ratio(coverage_pass, coverage_total)
        if cov is None:
            if gold_facts >= 1:
                errors.append(
                    "analytics_coverage_matrix.md has no applicable Status rows "
                    "(empty set is NOT_APPLICABLE, not 100%)"
                )
        else:
            print(f"Business-process coverage: {cov:.0%} (required >= {min_process:.0%})")
            if coverage_unknown:
                warnings.append(f"{coverage_unknown} coverage-matrix rows lack explicit Status")
            if cov < min_process:
                errors.append(
                    f"analytics_coverage_matrix coverage {cov:.0%} below required {min_process:.0%}"
                )

    if gold_facts >= 1 and not fact_contracts.exists():
        errors.append("missing fact_coverage_contracts.md for material analytical facts")
    else:
        fcov = ratio(fact_pass, fact_total)
        if fcov is None and gold_facts >= 1:
            errors.append("fact_coverage_contracts.md has no applicable Status rows")
        elif fcov is not None:
            print(f"Fact analytical coverage: {fcov:.0%} (required >= {fact_required:.0%})")
            if fcov < fact_required:
                errors.append(f"fact coverage {fcov:.0%} below required {fact_required:.0%}")

    if time_cov.exists():
        t_pass, t_total, _ = count_status_rows(time_cov)
        tcov = ratio(t_pass, t_total)
        if tcov is not None:
            print(f"Time-intelligence coverage: {tcov:.0%} (required >= {time_required:.0%})")
            if tcov < time_required:
                errors.append(
                    f"time-intelligence coverage {tcov:.0%} below required {time_required:.0%}"
                )
    elif gold_facts >= 1:
        warnings.append("missing time_intelligence_coverage.md")

    if obs_cov.exists():
        o_pass, o_total, _ = count_status_rows(obs_cov)
        ocov = ratio(o_pass, o_total)
        if ocov is not None:
            print(f"Observability domain coverage: {ocov:.0%} (required >= {dq_required:.0%})")
            if ocov < dq_required:
                errors.append(f"observability coverage {ocov:.0%} below required {dq_required:.0%}")
    elif gold_facts >= 1 and dq_count == 0 and not (insights / "data_observability_report.md").exists():
        errors.append("missing data observability coverage/report and DQ metric catalog")

    # Report traceability when presentation coverage artifact exists
    if figure_cov.exists():
        rendered = 0
        with_proof = 0
        for row in table_dicts(figure_cov):
            status = cell(row, "status").upper()
            if status != "RENDERED":
                continue
            rendered += 1
            proof = cell(row, "proof", "sql_proof", "proof_path")
            if proof and proof.upper() not in {"N/A", "TODO", ""}:
                with_proof += 1
        tcov = ratio(with_proof, rendered)
        if tcov is not None:
            print(f"Report traceability (RENDERED->proof): {tcov:.0%} (required >= {trace_required:.0%})")
            if tcov < trace_required:
                errors.append(
                    f"rendered proof traceability {tcov:.0%} below required {trace_required:.0%}"
                )
    # Reconciliation coverage is enforced in verify_metric_reconciliation.py using
    # critical_reconciliation_coverage_required (referenced here for gate visibility).
    print(f"Policy critical_reconciliation_coverage_required={recon_required:.0%}")

    if gold_facts >= 1 and measure_count == 0 and metric_count == 0:
        warnings.append("no business measures/metrics catalogued yet (informational)")

    if business_measure.exists() or business_metric.exists():
        if measure_path.exists() and metric_path.exists() and dq_count == 0 and pipeline_count == 0:
            warnings.append(
                "prefer separate data_quality_metric_catalog.md and pipeline_health_metric_catalog.md"
            )
    elif measure_path.exists() and "row_count" in read_text(measure_path).lower():
        warnings.append(
            "measure_catalog.md appears to mix model row_count / engineering QA with business measures"
        )

    # Advisory-only targets (never hard fail unless explicitly set and mode says so)
    adv_m = policy.get("advisory_measure_target")
    adv_t = policy.get("advisory_metric_target")
    if adv_m is not None and measure_count < int(adv_m):
        warnings.append(
            f"advisory measure target {adv_m} not met (have {measure_count}) — not a completion gate"
        )
    if adv_t is not None and metric_count < int(adv_t):
        warnings.append(
            f"advisory metric target {adv_t} not met (have {metric_count}) — not a completion gate"
        )

    return print_results("Analytics coverage check", errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
