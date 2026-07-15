#!/usr/bin/env python3
"""Check data observability domain coverage and quality/pipeline catalogs."""

from __future__ import annotations

import argparse
from pathlib import Path

from lib_gate_common import (
    REQUIRED_OBSERVABILITY_DOMAINS,
    cell,
    count_gold_facts,
    load_analytics_policy,
    named_status,
    normalize_header,
    print_results,
    ratio,
    read_text,
    table_dicts,
)


def observability_row_status(row: dict[str, str]) -> str:
    status = named_status(row)
    if status != "UNKNOWN":
        return status
    raw = cell(row, "status").strip().upper()
    if raw == "SUPPORTED":
        return "PASS"
    return status


def analytics_in_scope(root: Path) -> bool:
    insights = root / "reports" / "agent" / "09_analytics_insights"
    presentation = root / "reports" / "agent" / "10_presentation" / "matplotlib"
    return insights.exists() or presentation.exists() or count_gold_facts(root) > 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    policy = load_analytics_policy(root)
    required_ratio = float(policy.get("observability_domain_coverage_required", 1.0))

    insights = root / "reports" / "agent" / "09_analytics_insights"
    if not analytics_in_scope(root):
        print("SKIPPED: analytics not in scope")
        return 0

    coverage_path = insights / "data_observability_coverage.md"
    dq = insights / "kpis" / "data_quality_metric_catalog.md"
    pipeline = insights / "kpis" / "pipeline_health_metric_catalog.md"

    errors: list[str] = []
    warnings: list[str] = []

    if not coverage_path.exists():
        errors.append(
            "missing reports/agent/09_analytics_insights/data_observability_coverage.md "
            "while analytics insights, gold facts, or presentation exist"
        )
        return print_results("Data observability coverage check", errors, warnings)

    rows = table_dicts(coverage_path, required_any_headers=("domain", "status"))
    if not rows:
        rows = table_dicts(coverage_path)

    domain_rows: dict[str, dict[str, str]] = {}
    for row in rows:
        domain = normalize_header(cell(row, "domain", "observability_domain", "area"))
        if domain:
            domain_rows[domain] = row

    covered = 0
    applicable = len(REQUIRED_OBSERVABILITY_DOMAINS)
    for domain in sorted(REQUIRED_OBSERVABILITY_DOMAINS):
        norm_domain = normalize_header(domain)
        row = domain_rows.get(norm_domain)
        if row is None:
            errors.append(f"data_observability_coverage.md missing domain row: {domain}")
            continue
        status = observability_row_status(row)
        notes = cell(row, "notes", "reason", "comment", "comments", "evidence")
        if status == "NOT_APPLICABLE":
            if not notes:
                errors.append(f"{domain}: NOT_APPLICABLE requires Notes/reason")
            else:
                covered += 1
        elif status == "PASS":
            covered += 1
        elif status == "UNKNOWN":
            errors.append(f"{domain}: explicit Status required (PASS/SUPPORTED/NOT_APPLICABLE)")
        else:
            errors.append(f"{domain}: status {status} is not acceptable for observability coverage")

    cov = ratio(covered, applicable)
    if cov is not None:
        print(f"Observability domain coverage: {covered}/{applicable} ({cov:.0%})")
        if cov < required_ratio:
            errors.append(
                f"observability domain coverage {cov:.0%} below required {required_ratio:.0%}"
            )

    pipeline_row = domain_rows.get(normalize_header("pipeline reliability"))
    pipeline_na = pipeline_row is not None and observability_row_status(pipeline_row) == "NOT_APPLICABLE"

    if insights.exists() and not pipeline_na:
        if not dq.exists() or len(read_text(dq).strip()) < 40:
            errors.append(
                "missing or empty data_quality_metric_catalog.md while analytics is in scope"
            )
        if not pipeline.exists() or len(read_text(pipeline).strip()) < 40:
            errors.append(
                "missing or empty pipeline_health_metric_catalog.md "
                "(unless pipeline reliability is NOT_APPLICABLE in coverage)"
            )

    obs_report = insights / "data_observability_report.md"
    if not obs_report.exists():
        warnings.append("missing data_observability_report.md narrative report")

    return print_results("Data observability coverage check", errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
