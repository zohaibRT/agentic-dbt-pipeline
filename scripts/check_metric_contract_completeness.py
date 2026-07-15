#!/usr/bin/env python3
"""Check KPI / metric contract completeness for published metrics.

Validates every published KPI row independently against the canonical contract.
Coverage = complete critical KPI contracts / total published critical KPIs.
Empty published set is NOT 100%.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from lib_gate_common import (
    KNOWN_VALIDATION_TYPES,
    business_approval_status,
    cell,
    compute_contract_fingerprint,
    is_generic_blocker_text,
    is_meaningful_text,
    load_analytics_policy,
    normalize_header,
    parse_applicability,
    parse_markdown_tables,
    print_results,
    ratio,
    read_text,
    technical_verification_status,
    validate_sql_proof_file,
)

PUBLISHED_APPROVALS = {"APPROVED", "PROPOSED", "APPROVED_WITH_CONDITIONS"}
BLOCKED_APPROVALS = {"BLOCKED", "DEFERRED"}

ALLOWED_PLACEHOLDERS: dict[str, frozenset[str]] = {
    "target": frozenset({"target not defined"}),
    "caveats": frozenset({"none"}),
}

# Identity + always-required for APPROVED/PROPOSED (aliases).
APPROVED_REQUIRED = (
    ("kpi_id", ("kpi_id", "kpi", "id")),
    ("contract_version", ("contract_version", "contract version", "version")),
    ("display_name", ("display_name", "display")),
    ("metric_class", ("metric_class", "class")),
    ("business_process", ("business_process", "process")),
    ("business_question", ("business_question",)),
    ("decision_supported", ("decision_supported", "decisions_supported")),
    ("action_when_bad", ("action_when_bad", "action when bad", "recommended_action")),
    ("business_owner", ("business_owner", "owner")),
    ("approver", ("approver", "approved_by")),
    ("business_definition", ("business_definition", "business definition")),
    ("formula", ("formula",)),
    ("grain", ("grain",)),
    ("counting_key", ("counting_key", "count_key")),
    ("source_models", ("source_models", "source models", "source_model", "source model")),
    ("source_columns", ("source_columns", "source columns")),
    ("date_field", ("date_field", "date field")),
    ("date_role", ("date_role", "date role")),
    ("included_records", ("included_records", "included_rows", "included rows")),
    ("excluded_records", ("excluded_records", "excluded_rows", "excluded rows")),
    ("status_logic", ("status_logic", "status logic")),
    ("dimensions", ("dimensions",)),
    ("unit", ("unit", "unit_currency", "unit/currency")),
    ("format", ("format",)),
    ("precision", ("precision",)),
    ("aggregation_behavior", ("aggregation_behavior", "aggregation")),
    ("null_behavior", ("null_behavior", "null behavior")),
    ("refresh_frequency", ("refresh_frequency", "refresh frequency")),
    ("freshness_sla", ("freshness_sla", "freshness sla")),
    ("target", ("target",)),
    ("desired_direction", ("desired_direction", "desired direction")),
    ("validation_source", ("validation_source", "validation source")),
    ("validation_type", ("validation_type", "validation type")),
    ("reconciliation_tolerance", ("reconciliation_tolerance", "diff_tolerance", "diff_/_tolerance", "tolerance", "diff")),
    ("sql_proof", ("sql_proof", "sql proof", "proof", "verified_by_sql_proof")),
    ("expected_result", ("expected_result", "expected")),
    ("actual_result", ("actual_result", "actual")),
    ("technical_verification_status", ("technical_verification_status", "verification", "verification_status")),
    ("business_approval_status", ("business_approval_status", "approval", "approval_status")),
    ("approval_evidence", ("approval_evidence", "approval evidence", "evidence_path")),
    ("approval_date", ("approval_date", "approval date", "approved_at")),
    ("confidence", ("confidence",)),
    ("caveats", ("caveats", "why correct / open question", "reason")),
)

BLOCKED_REQUIRED = (
    ("kpi_id", ("kpi_id", "kpi", "id")),
    ("contract_version", ("contract_version", "contract version", "version")),
    ("display_name", ("display_name", "display")),
    ("metric_class", ("metric_class", "class")),
    ("business_process", ("business_process", "process")),
    ("business_question", ("business_question",)),
    ("reason", ("reason", "caveats", "reason/caveats", "why correct / open question")),
    ("missing_evidence", ("missing evidence", "missing_evidence")),
    ("business_owner", ("business_owner", "owner")),
    ("recommended_next_action", ("recommended_next_action", "next action", "next_action", "recommended next action")),
    ("review_or_resolution_condition", ("review_or_resolution_condition", "review condition", "review_condition")),
    ("business_approval_status", ("business_approval_status", "approval", "approval_status")),
    ("technical_verification_status", ("technical_verification_status", "verification", "verification_status")),
)

# Soft-required on expanded schema; legacy emits migration warning when absent as columns.
EXPANDED_OPTIONAL_COLUMNS = (
    "contract_fingerprint",
    "timezone",
    "currency",
    "numerator",
    "denominator",
    "zero_denominator_behavior",
    "target_source",
    "warning_threshold",
    "critical_threshold",
    "calculated_difference",
    "calculated_status",
    "approval_conditions",
    "approval_expiry_or_review_condition",
)


def contract_rows(path: Path) -> tuple[str, list[dict[str, str]], list[str]]:
    text = read_text(path)
    rows: list[dict[str, str]] = []
    schema = "unknown"
    headers_out: list[str] = []
    for headers, data in parse_markdown_tables(text):
        norm = [normalize_header(h) for h in headers]
        header_set = set(norm)
        if not (
            {"sql_proof", "approval", "approval_status", "business_approval_status"} & header_set
            or ("kpi_id" in header_set and "grain" in header_set)
            or ("kpi" in header_set and "sql_proof" in header_set)
        ):
            continue
        if {"business_definition", "validation_type", "contract_version"} & header_set:
            schema = "expanded"
        elif "sql_proof" in header_set:
            schema = "legacy"
        headers_out = norm
        for cells in data:
            row = {
                norm[i]: (cells[i].strip() if i < len(cells) else "")
                for i in range(len(norm))
                if norm[i]
            }
            rows.append(row)
        if rows:
            return schema, rows, headers_out
    return schema, rows, headers_out


def row_has(row: dict[str, str], aliases: tuple[str, ...], field_key: str | None = None) -> bool:
    value = cell(row, *aliases)
    if not value:
        return False
    applicability = parse_applicability(value)
    if applicability["status"] == "BLANK":
        return False
    if applicability["status"] == "BARE_NA":
        return False
    if applicability["status"] == "NOT_APPLICABLE":
        return True
    token = value.strip()
    upper = token.upper()
    if upper in {"TODO", "TBD", "<TODO>", ""}:
        return False
    placeholders = ALLOWED_PLACEHOLDERS.get(field_key or "", frozenset())
    if token.lower() in placeholders:
        return True
    return is_meaningful_text(token, allow_placeholders=placeholders)


def require_field_or_na(
    row: dict[str, str],
    kpi_id: str,
    label: str,
    aliases: tuple[str, ...],
    errors: list[str],
    *,
    required: bool,
) -> None:
    if not required:
        return
    value = cell(row, *aliases)
    applicability = parse_applicability(value)
    if applicability["status"] == "VALUE" and is_meaningful_text(value):
        return
    if applicability["status"] == "NOT_APPLICABLE":
        return
    if applicability["status"] == "BARE_NA":
        errors.append(f"{kpi_id}: {label} needs NOT_APPLICABLE: <specific reason>, not bare N/A")
        return
    errors.append(f"{kpi_id}: missing {label}")


def is_ratio_metric(row: dict[str, str]) -> bool:
    metric_class = cell(row, "metric_class", "class").lower()
    validation_type = cell(row, "validation_type", "validation type").lower()
    aggregation = cell(row, "aggregation", "aggregation_behavior").lower()
    format_token = cell(row, "format").lower()
    return (
        "ratio" in metric_class
        or validation_type.startswith("ratio_")
        or aggregation == "ratio"
        or format_token in {"percent", "percentage", "ratio"}
    )


def is_currency_format(row: dict[str, str]) -> bool:
    format_token = cell(row, "format").lower()
    unit = cell(row, "unit_currency", "unit/currency", "unit").lower()
    return format_token in {"currency", "money"} or "currency" in unit


def is_count_metric(row: dict[str, str]) -> bool:
    metric_class = cell(row, "metric_class", "class").lower()
    aggregation = cell(row, "aggregation", "aggregation_behavior").lower()
    format_token = cell(row, "format").lower()
    unit = cell(row, "unit", "unit_currency", "unit/currency").lower()
    return (
        "count" in metric_class
        or aggregation in {"count", "additive"}
        and format_token in {"integer", "count"}
        or unit in {"count", "integer"}
    ) and not is_ratio_metric(row)


def validate_conditional_fields(row: dict[str, str], kpi_id: str, errors: list[str]) -> None:
    if is_ratio_metric(row):
        require_field_or_na(row, kpi_id, "numerator", ("numerator",), errors, required=True)
        require_field_or_na(row, kpi_id, "denominator", ("denominator",), errors, required=True)
        require_field_or_na(
            row,
            kpi_id,
            "zero_denominator_behavior",
            ("zero_denominator_behavior", "zero denominator behavior"),
            errors,
            required=True,
        )
    else:
        # Counts must explicitly mark numerator/denominator N/A with reason when columns exist
        for label, aliases in (
            ("numerator", ("numerator",)),
            ("denominator", ("denominator",)),
            ("zero_denominator_behavior", ("zero_denominator_behavior", "zero denominator behavior")),
        ):
            if any(a.replace(" ", "_") in row or a in row for a in aliases) or cell(row, *aliases):
                require_field_or_na(row, kpi_id, label, aliases, errors, required=True)

    if is_currency_format(row):
        require_field_or_na(row, kpi_id, "currency", ("currency",), errors, required=True)
    elif cell(row, "currency") or "currency" in row:
        require_field_or_na(row, kpi_id, "currency", ("currency",), errors, required=True)

    target = cell(row, "target")
    target_app = parse_applicability(target)
    if target_app["status"] == "VALUE" and target.lower() not in {"target not defined"}:
        require_field_or_na(row, kpi_id, "target_source", ("target_source", "target source"), errors, required=True)

    approval = business_approval_status(row)
    if approval == "APPROVED_WITH_CONDITIONS":
        require_field_or_na(
            row,
            kpi_id,
            "approval_conditions",
            ("approval_conditions", "conditions"),
            errors,
            required=True,
        )
        require_field_or_na(
            row,
            kpi_id,
            "approval_expiry_or_review_condition",
            ("approval_expiry_or_review_condition", "review condition", "expiry"),
            errors,
            required=True,
        )

    # Timezone when date_field looks like a timestamp role
    date_role = cell(row, "date_role", "date role").lower()
    if "timestamp" in date_role or "timezone" in date_role or "tz" in date_role:
        require_field_or_na(row, kpi_id, "timezone", ("timezone", "tz"), errors, required=True)
    elif "timezone" in row or cell(row, "timezone"):
        require_field_or_na(row, kpi_id, "timezone", ("timezone", "tz"), errors, required=True)


def validate_definition_formula_separation(row: dict[str, str], kpi_id: str, errors: list[str]) -> None:
    definition = cell(row, "business_definition", "business definition").strip()
    formula = cell(row, "formula").strip()
    if definition and formula and definition.lower() == formula.lower():
        errors.append(
            f"{kpi_id}: business_definition and formula must not be the same value"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    policy = load_analytics_policy(root)
    required_ratio = float(policy.get("critical_kpi_contract_coverage_required", 1.0))

    contracts = root / "reports" / "agent" / "KPI_DEFINITION_CONTRACTS.md"
    insights = root / "reports" / "agent" / "09_analytics_insights"
    errors: list[str] = []
    warnings: list[str] = []

    if not contracts.exists() and not insights.exists():
        print("SKIPPED: no KPI contracts or analytics folder")
        return 0
    if not contracts.exists():
        errors.append(
            "KPI_DEFINITION_CONTRACTS.md missing while analytics insights exist — "
            "critical KPI contract coverage cannot be verified"
        )
        return print_results("Metric contract completeness check", errors, warnings)

    schema, rows, headers = contract_rows(contracts)
    print(f"Metric contract completeness: schema={schema} contract_rows={len(rows)}")

    if not rows:
        errors.append("KPI_DEFINITION_CONTRACTS.md has no data rows")
        return print_results("Metric contract completeness check", errors, warnings)

    if schema == "legacy":
        warnings.append(
            "legacy KPI contract schema detected — migrate to expanded canonical schema "
            "(see docs/kpi-contract-human-approval-migration.md)"
        )

    header_set = set(headers)
    published = 0
    complete = 0
    for index, row in enumerate(rows, start=1):
        kpi_id = cell(row, "kpi_id", "kpi", "id", "display_name") or f"row {index}"
        approval = business_approval_status(row)
        # Treat legacy APPROVED in Approval column as published
        legacy_approval = cell(row, "approval", "approval_status").upper()
        if approval == "PENDING_REVIEW" and legacy_approval in PUBLISHED_APPROVALS:
            approval = legacy_approval

        if approval in BLOCKED_APPROVALS or legacy_approval in BLOCKED_APPROVALS:
            published += 1
            missing = [
                label
                for label, aliases in BLOCKED_REQUIRED
                if not row_has(row, aliases, field_key=label)
            ]
            # Soft-require contract_version on blocked when column present or expanded
            if schema == "expanded" and not row_has(row, ("contract_version", "version")):
                if "contract_version" not in missing:
                    missing.append("contract_version")
            if schema == "expanded" and not row_has(row, ("metric_class", "class")):
                if "metric_class" not in missing:
                    missing.append("metric_class")
            reason = cell(row, "reason", "caveats", "why correct / open question")
            if is_generic_blocker_text(reason):
                errors.append(
                    f"{kpi_id}: BLOCKED/DEFERRED reason is generic — explain what/why/missing/"
                    "owner/action/condition"
                )
            if missing:
                errors.append(f"{kpi_id}: BLOCKED/DEFERRED missing fields: {', '.join(missing)}")
            else:
                complete += 1
            continue

        if approval not in PUBLISHED_APPROVALS and legacy_approval not in PUBLISHED_APPROVALS:
            tech_early = technical_verification_status(row)
            # Technically verified rows with blank approval still need an explicit
            # business_approval_status — do not silently skip them.
            if tech_early in {"PASS", "WARN"} and row_has(row, ("formula",)):
                errors.append(f"{kpi_id}: missing business_approval_status")
                published += 1
                continue
            if approval in {"", "DRAFT", "PENDING", "PENDING_REVIEW", "NOT_REQUESTED"}:
                continue
            warnings.append(f"{kpi_id}: unusual approval status {approval}")
            continue

        published += 1

        # Legacy soft fields: contract_version / source_columns / status_logic may be absent as columns
        required = list(APPROVED_REQUIRED)
        if schema == "legacy":
            skip_on_legacy = {
                "contract_version",
                "approver",
                "business_definition",
                "source_columns",
                "status_logic",
                "precision",
                "null_behavior",
                "refresh_frequency",
                "freshness_sla",
                "validation_source",
                "validation_type",
                "approval_evidence",
                "approval_date",
                "confidence",
            }
            required = [(k, a) for k, a in required if k not in skip_on_legacy]
            if "business_definition" not in header_set:
                warnings.append(
                    f"{kpi_id}: legacy schema missing Business Definition — migration required"
                )
            if "validation_type" not in header_set:
                warnings.append(
                    f"{kpi_id}: legacy schema missing Validation Type — migration required"
                )

        missing_critical = [
            label for label, aliases in required if not row_has(row, aliases, field_key=label)
        ]

        # Expanded schema always requires validation_type
        if schema == "expanded" and not row_has(row, ("validation_type", "validation type")):
            if "validation_type" not in missing_critical:
                missing_critical.append("validation_type")

        if missing_critical:
            errors.append(f"{kpi_id}: missing critical contract fields: {', '.join(missing_critical)}")
            continue

        validate_definition_formula_separation(row, kpi_id, errors)
        validate_conditional_fields(row, kpi_id, errors)

        vtype = cell(row, "validation_type", "validation type").lower()
        if vtype and vtype not in KNOWN_VALIDATION_TYPES:
            errors.append(f"{kpi_id}: unknown validation_type {vtype!r}")

        tech = technical_verification_status(row)
        if tech == "UNKNOWN" or not tech:
            errors.append(f"{kpi_id}: missing technical_verification_status")
        biz = business_approval_status(row)
        if not biz or biz == "UNKNOWN":
            errors.append(f"{kpi_id}: missing business_approval_status")

        # Fingerprint: if column present, must match calculated
        recorded_fp = cell(row, "contract_fingerprint", "fingerprint")
        calculated_fp = compute_contract_fingerprint(row)
        if recorded_fp and recorded_fp.lower() not in {"n/a", "todo", "none"}:
            if recorded_fp.strip() != calculated_fp:
                warnings.append(
                    f"{kpi_id}: contract_fingerprint stale "
                    f"(recorded={recorded_fp}, calculated={calculated_fp})"
                )

        proof_ref = cell(row, "sql_proof", "sql proof", "proof")
        proof_result = validate_sql_proof_file(
            root,
            proof_ref,
            expected_kpi_id=kpi_id if schema == "expanded" else None,
            require_validation_type=schema == "expanded",
            require_tolerance=vtype in {"numeric_tolerance", "ratio_tolerance"} and schema == "expanded",
        )
        if proof_result.get("errors"):
            errors.append(f"{kpi_id}: SQL proof issues: {'; '.join(proof_result['errors'])}")
        elif not any(err.startswith(f"{kpi_id}:") for err in errors):
            complete += 1

    cov = ratio(complete, published)
    if cov is None:
        errors.append(
            "no published critical KPI rows to score (empty applicable set is NOT_APPLICABLE, not 100%)"
        )
    else:
        print(f"Critical KPI contract coverage: {complete}/{published} ({cov:.0%})")
        if cov < required_ratio:
            errors.append(
                f"critical KPI contract coverage {cov:.0%} below required {required_ratio:.0%}"
            )

    return print_results("Metric contract completeness check", errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
