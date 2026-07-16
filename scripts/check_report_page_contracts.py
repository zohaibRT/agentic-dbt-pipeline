#!/usr/bin/env python3
"""Check report page contracts cover rendered presentation pages with stable page_ids."""

from __future__ import annotations

import argparse
from pathlib import Path

from lib_gate_common import (
    add_output_json_arg,
    cell,
    count_gold_facts,
    extract_page_ids_from_presentation,
    is_meaningful_text,
    list_gold_dimension_names,
    load_analytics_policy,
    load_json_registry,
    load_presentation_policy,
    normalize_header,
    presentation_registry_paths,
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
    text = " ".join(page_tokens(row) | {cell(row, "page_class", "class").lower()}).lower()
    return "executive" in text or cell(row, "page_class").lower() == "executive_overview"


def is_dq_page(row: dict[str, str]) -> bool:
    text = " ".join(page_tokens(row) | {cell(row, "page_class").lower()}).lower()
    return any(token in text for token in ("quality", "exception", "dq", "exceptions_quality"))


def is_pipeline_page(row: dict[str, str]) -> bool:
    text = " ".join(page_tokens(row) | {cell(row, "page_class").lower()}).lower()
    return "pipeline" in text


def is_dimensions_page(row: dict[str, str]) -> bool:
    text = " ".join(page_tokens(row) | {cell(row, "page_class").lower()}).lower()
    return "dimension" in text


def _na_ok(value: str) -> bool:
    """NOT_APPLICABLE allowed only with a reason."""
    text = (value or "").strip()
    if not text:
        return False
    upper = text.upper()
    if upper in {"N/A", "NA", "NONE", "NOT_APPLICABLE"}:
        return False
    if upper.startswith("NOT_APPLICABLE"):
        return ":" in text or len(text) > len("NOT_APPLICABLE") + 2
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_output_json_arg(parser)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--phase", choices=("analytics", "presentation", "final"), default="presentation")
    args = parser.parse_args()
    root = args.root.resolve()
    policy = load_analytics_policy(root)
    presentation_policy = load_presentation_policy(root)
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
            return print_results("Report page contracts check", errors, warnings, output_json=getattr(args, "output_json", None), validator_id=Path(__file__).stem)
        print("SKIPPED: report_page_contracts.md not found yet")
        return 0

    rows = table_dicts(
        contracts,
        required_any_headers=("page", "page_name", "page_id", "audience"),
    )
    if not rows:
        errors.append("report_page_contracts.md has no page rows")
        return print_results("Report page contracts check", errors, warnings, output_json=getattr(args, "output_json", None), validator_id=Path(__file__).stem)

    rendered_pages = extract_page_ids_from_presentation(root)
    # Prefer page_registry when present
    paths = presentation_registry_paths(root)
    page_reg = load_json_registry(paths["page_registry.json"])
    registry_page_ids: set[str] = set()
    if isinstance(page_reg, dict):
        seen_reg: set[str] = set()
        for entry in page_reg.get("pages") or []:
            if not isinstance(entry, dict):
                continue
            pid = str(entry.get("page_id") or "").strip()
            if not pid:
                continue
            key = normalize_header(pid)
            if key in seen_reg:
                errors.append(f"duplicate page_id in page_registry.json: {pid}")
            seen_reg.add(key)
            registry_page_ids.add(key)
            registry_page_ids.add(pid.lower())
            rendered_pages.add(key)
            rendered_pages.add(pid.lower())

    print(f"Report page contracts: rows={len(rows)}, rendered_pages~{len(rendered_pages)}")

    contract_tokens: set[str] = set()
    covered_rendered: set[str] = set()
    complete_contracts = 0
    page_ids_seen: set[str] = set()

    required_fields = (
        ("page_id", ("page_id", "page id")),
        ("page_name", ("page_name", "page name", "page")),
        ("audience", ("audience",)),
        ("page_class", ("page_class", "page class", "class")),
        ("business_processes", ("business process", "business_process", "business_processes", "business purpose", "purpose")),
        ("business_questions", ("business questions", "business_questions", "questions")),
        ("decisions_supported", ("decision", "decisions_supported", "decisions supported")),
        ("primary_kpis", ("primary kpi", "primary_kpis", "primary kpis")),
        ("driver_metrics", ("driver", "driver_metrics", "driver metrics")),
        ("guardrail_metrics", ("guardrail", "guardrail_metrics", "guardrail metrics")),
        ("dimensions", ("dimension", "dimensions")),
        ("filters", ("filter", "filters")),
        ("reporting_period", ("time_period", "reporting period", "period", "time period")),
        ("visuals", ("visual", "visuals")),
        ("exceptions", ("exception", "exceptions")),
        ("insight_narrative", ("insight", "insight_narrative", "insight narrative")),
        ("recommended_actions", ("recommended action", "recommended actions", "action")),
        ("caveats", ("caveat", "caveats")),
        ("technical_validation_status", ("technical_validation_status", "validation status", "validation_status", "status")),
        ("business_approval_status", ("business_approval_status", "business approval status", "approval")),
    )

    # Fields that may be N/A with reason on non-executive dictionary pages
    soft_na_pages = {"metric_dictionary", "dimension_explorer", "report_information", "all_measures", "all_metrics", "all_dimensions"}

    for index, row in enumerate(rows, start=1):
        tokens = page_tokens(row)
        if not tokens:
            errors.append(f"contract row {index}: missing Page ID / Page Name")
            continue
        contract_tokens.update(tokens)

        page_id = cell(row, "page_id", "page id") or cell(row, "page_name", "page name", "page")
        page_key = normalize_header(page_id)
        if page_key in page_ids_seen:
            errors.append(f"duplicate page_id: {page_id}")
        page_ids_seen.add(page_key)

        page_label = page_id or f"row {index}"
        page_class = cell(row, "page_class", "page class", "class").lower() or page_key
        missing: list[str] = []
        for label, aliases in required_fields:
            value = cell(row, *aliases)
            if not value:
                # Legacy fixtures may omit newer columns — require at final / when policy strict
                if label in {
                    "page_id",
                    "page_name",
                    "audience",
                    "business_processes",
                    "decisions_supported",
                    "primary_kpis",
                    "reporting_period",
                    "exceptions",
                    "recommended_actions",
                    "technical_validation_status",
                }:
                    missing.append(label)
                elif args.phase == "final":
                    missing.append(label)
                elif label in {
                    "page_class",
                    "business_questions",
                    "driver_metrics",
                    "guardrail_metrics",
                    "dimensions",
                    "filters",
                    "visuals",
                    "insight_narrative",
                    "caveats",
                    "business_approval_status",
                }:
                    warnings.append(f"{page_label}: missing optional-until-final field {label}")
                continue
            if not _na_ok(value) and label not in {"technical_validation_status", "business_approval_status"}:
                # bare N/A without reason
                if page_class in soft_na_pages or page_key in soft_na_pages:
                    errors.append(f"{page_label}: {label}={value!r} requires NOT_APPLICABLE with reason")
                elif value.upper() in {"N/A", "NA", "NONE", "NOT_APPLICABLE"}:
                    errors.append(f"{page_label}: {label}={value!r} requires NOT_APPLICABLE with reason")

        if missing:
            errors.append(f"{page_label}: incomplete page contract — missing {', '.join(missing)}")
        else:
            complete_contracts += 1

        if is_executive_page(row):
            if not cell(row, "primary_kpis", "primary kpi", "primary kpis"):
                errors.append(f"{page_label}: executive page requires Primary KPIs")
            # DQ on executive without guardrail classification
            primary = cell(row, "primary_kpis", "primary kpi", "primary kpis").lower()
            guardrail = cell(row, "guardrail_metrics", "guardrail", "guardrail metrics").lower()
            for token in ("orphan", "dq-", "data quality", "null_key", "pipeline", "build_success"):
                if token in primary and token not in guardrail and "guardrail" not in primary:
                    # only fail when clearly DQ/pipeline metric in primary and not listed as guardrail
                    if any(g in primary for g in ("orphan", "dq-", "null_key", "build_success", "failed_test")):
                        if not is_meaningful_text(guardrail) or guardrail.upper().startswith("NOT_APPLICABLE"):
                            errors.append(
                                f"{page_label}: data-quality/pipeline metric on executive page "
                                f"without guardrail classification"
                            )
                            break

        # HITL: technical PASS != business APPROVED
        tech = cell(row, "technical_validation_status", "validation status", "status").upper()
        biz = cell(row, "business_approval_status", "business approval status", "approval").upper()
        if tech == "PASS" and biz and biz not in {
            "APPROVED",
            "APPROVED_WITH_CONDITIONS",
            "PENDING_REVIEW",
            "NOT_REQUESTED",
            "PASS",  # legacy fixtures using Status column
        }:
            warnings.append(f"{page_label}: unusual business_approval_status={biz}")

    for rendered in rendered_pages:
        if page_is_covered(rendered, contract_tokens):
            covered_rendered.add(rendered)

    gold_facts = count_gold_facts(root)
    # Classification-driven dimension detection (not dim_* filesystem helpers alone)
    has_dims = bool(list_gold_dimension_names(root))
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
        errors.append(
            "Dimensions page contract required when classified dimension resources exist "
            "(detection uses classification/manifest unique_id, not filename helpers alone)"
        )

    uncovered = sorted(rendered_pages - covered_rendered)
    # Filter noisy HTML ids that are not pages
    noise = {
        "app", "root", "main", "content", "nav", "sidebar", "header", "footer",
        "chart", "card", "script", "style",
    }
    uncovered = [u for u in uncovered if u not in noise and not u.startswith("chart_") and not u.startswith("card_")]
    if uncovered and presentation_policy.get("require_bidirectional_page_contract_mapping", True):
        # Only fail on clear page-like tokens
        page_like = [
            u
            for u in uncovered
            if any(
                token in u
                for token in (
                    "executive",
                    "overview",
                    "pipeline",
                    "quality",
                    "exception",
                    "dimension",
                    "measure",
                    "metric",
                    "all_",
                )
            )
            or u in registry_page_ids
        ]
        if page_like:
            errors.append(f"rendered pages missing contracts: {', '.join(page_like[:12])}")

    orphan_contracts = []
    contract_page_ids = set()
    for row in rows:
        pid = normalize_header(cell(row, "page_id", "page id") or "")
        if pid:
            contract_page_ids.add(pid)
    # Rendered page ids from registry (preferred) plus explicit PAGE_IDS in builder
    rendered_keys = {normalize_header(p) for p in rendered_pages}
    if registry_page_ids:
        rendered_keys |= {normalize_header(p) for p in registry_page_ids}
    for row in rows:
        pid = normalize_header(cell(row, "page_id", "page id") or "")
        if not pid:
            continue
        if rendered_keys and pid not in rendered_keys:
            # Also allow match via page name slug present in rendered set
            name_slug = normalize_header(cell(row, "page_name", "page name", "page"))
            if name_slug not in rendered_keys:
                orphan_contracts.append(cell(row, "page_name", "page name", "page_id", "page") or pid)
    if orphan_contracts and rendered_keys:
        msg = f"orphan page contracts (no rendered page): {', '.join(orphan_contracts[:8])}"
        if args.phase == "final" and presentation_policy.get("require_bidirectional_page_contract_mapping", True):
            errors.append(msg)
        else:
            warnings.append(msg)

    cov = ratio(complete_contracts, len(rows))
    if cov is not None:
        print(f"Report page contract field coverage: {complete_contracts}/{len(rows)} ({cov:.0%})")
        if cov < required_ratio:
            errors.append(
                f"report page contract coverage {cov:.0%} below required {required_ratio:.0%}"
            )

    return print_results("Report page contracts check", errors, warnings, output_json=getattr(args, "output_json", None), validator_id=Path(__file__).stem)


if __name__ == "__main__":
    raise SystemExit(main())
