#!/usr/bin/env python3
"""Check report page contracts cover rendered presentation pages."""

from __future__ import annotations

import argparse
from pathlib import Path

from lib_gate_common import (
    cell,
    count_gold_facts,
    extract_page_ids_from_presentation,
    list_gold_fact_names,
    load_analytics_policy,
    normalize_header,
    print_results,
    ratio,
    read_text,
    table_dicts,
)


def page_tokens(row: dict[str, str]) -> set[str]:
    tokens: set[str] = set()
    for alias in ("page_id", "page name", "page_name", "page", "tab", "tab_name", "tab_id"):
        value = cell(row, alias)
        if not value:
            continue
        tokens.add(normalize_header(value))
        tokens.add(value.strip().lower())
    return {t for t in tokens if t}


def page_is_covered(rendered: str, contract_tokens: set[str]) -> bool:
    rendered_norm = normalize_header(rendered)
    rendered_lower = rendered.strip().lower()
    return (
        rendered in contract_tokens
        or rendered_norm in contract_tokens
        or rendered_lower in contract_tokens
    )


def is_executive_page(row: dict[str, str]) -> bool:
    text = " ".join(page_tokens(row)).lower()
    return "executive" in text or "overview" in text


def is_dq_page(row: dict[str, str]) -> bool:
    text = " ".join(page_tokens(row)).lower()
    return any(token in text for token in ("quality", "exception", "dq", "data quality"))


def is_pipeline_page(row: dict[str, str]) -> bool:
    text = " ".join(page_tokens(row)).lower()
    return "pipeline" in text


def is_dimensions_page(row: dict[str, str]) -> bool:
    text = " ".join(page_tokens(row)).lower()
    return "dimension" in text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    policy = load_analytics_policy(root)
    required_ratio = float(policy.get("report_page_contract_coverage_required", 1.0))

    presentation = root / "reports" / "agent" / "10_presentation"
    matplotlib = presentation / "matplotlib"
    if not presentation.exists():
        print("SKIPPED: no presentation folder")
        return 0

    contracts = presentation / "report_page_contracts.md"
    errors: list[str] = []
    warnings: list[str] = []

    if not contracts.exists():
        if matplotlib.exists():
            errors.append(
                "missing report_page_contracts.md while Matplotlib presentation exists"
            )
            return print_results("Report page contracts check", errors, warnings)
        print("SKIPPED: report_page_contracts.md not found yet")
        return 0

    rows = table_dicts(
        contracts,
        required_any_headers=("page", "page_name", "page_id", "audience"),
    )
    if not rows:
        errors.append("report_page_contracts.md has no page rows")
        return print_results("Report page contracts check", errors, warnings)

    rendered_pages = extract_page_ids_from_presentation(root)
    print(f"Report page contracts: rows={len(rows)}, rendered_pages~{len(rendered_pages)}")

    contract_tokens: set[str] = set()
    covered_rendered: set[str] = set()
    complete_contracts = 0

    required_fields = (
        ("audience", ("audience",)),
        ("business_purpose", ("business purpose", "purpose", "business_process")),
        ("decisions_supported", ("decision", "decisions_supported", "decisions supported")),
        ("primary_kpis", ("primary kpi", "primary_kpis", "primary kpis")),
        ("time_period", ("time_period", "reporting period", "period", "time period")),
        ("exceptions", ("exception", "exceptions")),
        ("recommended_actions", ("recommended action", "recommended actions", "action")),
    )

    for index, row in enumerate(rows, start=1):
        tokens = page_tokens(row)
        if not tokens:
            errors.append(f"contract row {index}: missing Page ID / Page Name")
            continue
        contract_tokens.update(tokens)

        missing = [
            label
            for label, aliases in required_fields
            if not cell(row, *aliases)
        ]
        page_label = cell(row, "page_name", "page name", "page_id", "page") or f"row {index}"
        if missing:
            errors.append(f"{page_label}: missing required contract fields: {', '.join(missing)}")
        else:
            complete_contracts += 1

        if is_executive_page(row) and not cell(row, "primary_kpis", "primary kpi", "primary kpis"):
            errors.append(f"{page_label}: executive page requires Primary KPIs")

    for rendered in rendered_pages:
        if page_is_covered(rendered, contract_tokens):
            covered_rendered.add(rendered)

    gold_facts = count_gold_facts(root)
    has_dims = any(name.startswith("dim_") for name in list_gold_fact_names(root))
    insights = root / "reports" / "agent" / "09_analytics_insights"
    dq_catalog = insights / "kpis" / "data_quality_metric_catalog.md"
    pipeline_catalog = insights / "kpis" / "pipeline_health_metric_catalog.md"
    has_dq = dq_catalog.exists() and len(read_text(dq_catalog).strip()) > 40
    has_pipeline = pipeline_catalog.exists() and len(read_text(pipeline_catalog).strip()) > 40

    if (gold_facts >= 1 or has_dq) and not any(is_dq_page(row) for row in rows):
        errors.append("Exceptions/Data Quality page contract required when gold facts or DQ catalog exist")
    if (gold_facts >= 1 or has_pipeline) and not any(is_pipeline_page(row) for row in rows):
        errors.append("Pipeline Health page contract required when gold facts or pipeline catalog exist")
    if has_dims and not any(is_dimensions_page(row) for row in rows):
        errors.append("Dimensions page contract required when gold dimension models exist")

    uncovered = sorted(rendered_pages - covered_rendered)
    if uncovered:
        errors.append(f"rendered pages missing contracts: {', '.join(uncovered[:12])}")

    orphan_contracts = []
    for row in rows:
        tokens = page_tokens(row)
        if rendered_pages and not any(page_is_covered(rendered, tokens) for rendered in rendered_pages):
            orphan_contracts.append(cell(row, "page_name", "page name", "page_id", "page") or "unknown")
    if orphan_contracts and rendered_pages:
        warnings.append(f"contract pages not found in presentation: {', '.join(orphan_contracts[:8])}")

    cov = ratio(complete_contracts, len(rows))
    if cov is not None:
        print(f"Report page contract field coverage: {complete_contracts}/{len(rows)} ({cov:.0%})")
        if cov < required_ratio:
            errors.append(
                f"report page contract coverage {cov:.0%} below required {required_ratio:.0%}"
            )

    return print_results("Report page contracts check", errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
