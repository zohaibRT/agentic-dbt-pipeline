#!/usr/bin/env python3
"""Verify KPI contracts with independent reconciliation.

Parses columns by header. Calculates variance/set/row-count/acceptance-rule
results independently and fails when recorded PASS contradicts calculation.
"""

from __future__ import annotations

import argparse
from decimal import Decimal
from pathlib import Path
from typing import Any

from lib_gate_common import (
    add_output_json_arg,
    KNOWN_VALIDATION_TYPES,
    business_approval_status,
    cell,
    compute_contract_fingerprint,
    evaluate_typed_acceptance_rule,
    find_valid_waiver_for_kpi,
    load_analytics_policy,
    normalize_header,
    parse_markdown_tables,
    parse_number,
    parse_tolerance,
    print_results,
    ratio,
    read_text,
    reconcile_acceptance_rule,
    reconcile_numeric,
    reconcile_row_count,
    reconcile_set_match,
    resolve_proof_path,
    technical_verification_status,
    validate_sql_proof_file,
)

KPI_CONTRACTS = Path("reports/agent/KPI_DEFINITION_CONTRACTS.md")
METRIC_MATRIX = Path("reports/agent/METRIC_VERIFICATION_MATRIX.md")
BAD_STATUSES = {"FAIL", "BLOCKED"}
VALID_STATUSES = {"PASS", "WARN", "FAIL", "BLOCKED", "DEFERRED", "SKIPPED"}
NUMERIC_TYPES = {
    "numeric_exact",
    "numeric_tolerance",
    "ratio_tolerance",
}


def detect_contract_schema(headers: list[str]) -> str:
    norm = {normalize_header(h) for h in headers}
    if "validation_type" in norm or "business_definition" in norm or "contract_version" in norm:
        return "expanded"
    if {"display_name", "business_question", "counting_key", "decision_supported"} & norm:
        # Expanded-shaped headers without new columns → treat as legacy_with_verification
        if "sql_proof" in norm:
            return "legacy_with_verification"
        return "legacy"
    if "sql_proof" in norm or "approval_status" in norm or "approval" in norm:
        if {"verification", "verification_status", "expected", "expected_result"} & norm:
            return "legacy_with_verification"
        return "legacy"
    return "unknown"


def rows_from_first_matching_table(path: Path, matcher) -> tuple[str, list[dict[str, str]]]:
    text = read_text(path)
    for headers, data in parse_markdown_tables(text):
        schema = matcher(headers)
        if schema == "unknown":
            continue
        norm_headers = [normalize_header(h) for h in headers]
        rows: list[dict[str, str]] = []
        for cells in data:
            if not cells or cells[0].upper() == "TODO":
                continue
            row = {
                norm_headers[i]: (cells[i].strip() if i < len(cells) else "")
                for i in range(len(norm_headers))
                if norm_headers[i]
            }
            rows.append(row)
        return schema, rows
    return "unknown", []


def proof_hard_check(
    root: Path,
    label: str,
    proof_ref: str,
    errors: list[str],
    *,
    expected_kpi_id: str | None = None,
    require_validation_type: bool = False,
    require_tolerance: bool = False,
) -> bool:
    result = validate_sql_proof_file(
        root,
        proof_ref,
        expected_kpi_id=expected_kpi_id,
        require_validation_type=require_validation_type,
        require_tolerance=require_tolerance,
    )
    if not result.get("exists"):
        errors.append(f"{label}: referenced SQL proof not found: {proof_ref}")
        return False
    for err in result.get("errors") or []:
        errors.append(f"{label}: {err}")
    ok = bool(
        result.get("has_sql")
        and result.get("has_expected")
        and result.get("has_captured")
        and result.get("has_status")
    )
    if not ok and not result.get("errors"):
        errors.append(f"{label}: SQL proof incomplete at {result.get('path')}")
    return ok and not result.get("errors")


def numeric_reconcile_row(
    label: str,
    expected: str,
    actual: str,
    tolerance: str,
    recorded_status: str,
    recorded_diff: str,
    errors: list[str],
    warnings: list[str],
    *,
    validation_type: str = "numeric_tolerance",
    root: Path | None = None,
    fingerprint: str = "",
    waiver_disclosures: list[Any] | None = None,
) -> bool:
    """Return True when reconciliation succeeds within tolerance or has a valid waiver.

    Calculated FAIL never becomes technical PASS. A valid waiver yields governed
    exception coverage while preserving calculated_status=FAIL in disclosures.
    """
    tol_info = parse_tolerance(tolerance or ("exact" if validation_type == "numeric_exact" else "0"))
    if validation_type == "numeric_exact":
        tol_info = parse_tolerance("exact")
    if tol_info["kind"] == "acceptance_rule" and validation_type in NUMERIC_TYPES | {"row_count_match"}:
        errors.append(f"{label}: invalid or ambiguous tolerance {tolerance!r}")
        return False
    if tol_info["kind"] in {"absolute", "relative"} and tol_info["value"] is None:
        errors.append(f"{label}: invalid tolerance {tolerance!r}")
        return False

    result = reconcile_numeric(
        expected,
        actual,
        "exact" if validation_type == "numeric_exact" else (tolerance or "0"),
    )
    calc = result["calculated_status"]
    if result["expected"] is None or result["actual"] is None:
        if not expected or not actual:
            errors.append(f"{label}: missing expected or actual for numeric reconciliation")
            return False
        # Nonnumeric values require an explicit non-numeric validation_type; never bypass via WARN.
        if validation_type in NUMERIC_TYPES | {"row_count_match", ""}:
            errors.append(
                f"{label}: nonnumeric expected/actual for {validation_type or 'numeric'} "
                "reconciliation — set validation_type to set_match/acceptance_rule or fix values"
            )
            return False
        errors.append(f"{label}: expected/actual not parseable for validation_type={validation_type}")
        return False

    if recorded_diff and recorded_diff.upper() not in {"N/A", "TODO", "NONE", ""}:
        parsed_diff = parse_number(recorded_diff.replace("±", "").split()[0])
        if parsed_diff is not None and result["abs_diff"] is not None:
            if abs(parsed_diff - result["abs_diff"]) > Decimal("0.01") and "relative" not in (
                tolerance or ""
            ).lower():
                errors.append(
                    f"{label}: recorded Diff {recorded_diff!r} does not match "
                    f"calculated abs_diff {result['abs_diff']}"
                )

    if recorded_status == "PASS" and calc == "FAIL":
        errors.append(
            f"{label}: recorded Verification PASS contradicts calculated variance "
            f"(expected={expected!r}, actual={actual!r}, abs_diff={result['abs_diff']}, "
            f"tolerance={tolerance!r})"
        )
        return False
    if calc == "FAIL" and recorded_status not in {"FAIL", "BLOCKED", "WARN"}:
        errors.append(f"{label}: calculated reconciliation FAIL but status is {recorded_status}")
        return False
    if calc == "PASS":
        return True

    # calc == FAIL: require formal waiver bound to type/result/diff/tolerance/fingerprint
    if root is not None:
        waiver, werrs, disposition = find_valid_waiver_for_kpi(
            root,
            label,
            fingerprint=fingerprint,
            validation_type=validation_type,
            calculated_status="FAIL",
            calculated_difference=result.get("abs_diff"),
            tolerance=tolerance or "0",
        )
        if waiver and disposition == "APPROVED_WAIVER":
            entry = {
                "kpi_id": label,
                "waiver_id": waiver.waiver_id,
                "calculated_status": "FAIL",
                "governance_disposition": "APPROVED_WAIVER",
                "validation_type": validation_type,
                "calculated_difference": str(result.get("abs_diff")),
                "tolerance": tolerance or "0",
                "fingerprint": fingerprint,
            }
            msg = (
                f"{label}: calculated_status=FAIL governance_disposition=APPROVED_WAIVER "
                f"(waiver_id={waiver.waiver_id}, abs_diff={result['abs_diff']})"
            )
            warnings.append(msg)
            if waiver_disclosures is not None:
                waiver_disclosures.append(entry)
            return True  # governed exception counts toward coverage, not technical PASS
        errors.extend(werrs or [f"{label}: reconciliation FAIL/WARN without valid waiver"])
        return False

    if recorded_status == "WARN":
        errors.append(f"{label}: reconciliation WARN without formal waiver register lookup")
        return False
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_output_json_arg(parser)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()

    root = args.root.resolve()
    policy = load_analytics_policy(root)
    recon_required = float(policy.get("critical_reconciliation_coverage_required", 1.0))
    errors: list[str] = []
    warnings: list[str] = []

    contracts_path = root / KPI_CONTRACTS
    matrix_path = root / METRIC_MATRIX

    schema = "unknown"
    contracts: list[dict[str, str]] = []
    if not contracts_path.exists():
        errors.append(f"Missing {KPI_CONTRACTS}")
    else:
        schema, contracts = rows_from_first_matching_table(contracts_path, detect_contract_schema)
        if schema == "unknown":
            errors.append("KPI_DEFINITION_CONTRACTS.md has no recognizable contract table headers")
        elif not contracts:
            errors.append("KPI definition contracts file has no contract rows")
        else:
            print(f"Detected KPI contract schema: {schema}")
            if schema.startswith("legacy"):
                warnings.append("legacy KPI contract schema detected — migrate to expanded schema")

    matrix: list[dict[str, str]] = []
    if not matrix_path.exists():
        errors.append(f"Missing {METRIC_MATRIX}")
    else:
        _schema, matrix = rows_from_first_matching_table(
            matrix_path,
            lambda headers: "legacy"
            if {"status", "recorded_technical_status", "expected_result", "expected"}
            & {normalize_header(h) for h in headers}
            else "unknown",
        )
        if not matrix:
            errors.append("Metric verification matrix has no metric rows")

    critical_total = 0
    critical_reconciled = 0
    blocked_or_deferred = 0
    governed_exceptions: list[dict[str, Any]] = []

    for index, row in enumerate(contracts, start=1):
        kpi_id = (
            cell(row, "kpi_id", "kpi", "id", "key_performance_indicator", "display_name")
            or f"KPI row {index}"
        )
        approval = business_approval_status(row)
        legacy_approval = cell(row, "approval", "approval_status").upper()
        if approval == "PENDING_REVIEW" and legacy_approval in {"APPROVED", "PROPOSED"}:
            approval = legacy_approval

        verification = technical_verification_status(row)
        proof = cell(row, "sql_proof", "verified_by_sql_proof", "proof")
        expected = cell(row, "expected", "expected_result", "acceptance_rule")
        actual = cell(row, "actual", "actual_result")
        tolerance = cell(
            row,
            "diff_tolerance",
            "diff_/_tolerance",
            "tolerance",
            "reconciliation_tolerance",
            "diff",
        )
        validation_type = cell(row, "validation_type", "recon_type", "contract_validation_type").lower()
        recorded_diff = cell(row, "calculated_difference", "diff", "difference", "abs_diff")

        if approval in {"BLOCKED", "DEFERRED"} or legacy_approval in {"BLOCKED", "DEFERRED"}:
            blocked_or_deferred += 1
            reason = cell(row, "reason", "why_correct_/_open_question", "caveats")
            if not reason:
                errors.append(f"{kpi_id}: BLOCKED/DEFERRED requires reason / missing evidence")
            blocker_evidence = cell(row, "missing_evidence", "blocker_evidence", "sql_proof", "proof")
            if blocker_evidence and resolve_proof_path(root, blocker_evidence) is None:
                # Allow non-path evidence text for blockers
                if "/" in blocker_evidence or blocker_evidence.endswith(".md") or blocker_evidence.endswith(".sql"):
                    errors.append(f"{kpi_id}: blocker/deferred proof artifact not found: {blocker_evidence}")
            continue

        if approval in {"APPROVED", "PROPOSED", "APPROVED_WITH_CONDITIONS"} or (
            not legacy_approval and verification in {"PASS", "WARN"}
        ):
            critical_total += 1
            if verification not in VALID_STATUSES:
                errors.append(f"{kpi_id}: invalid or missing verification status '{verification}'")
                continue
            if verification in BAD_STATUSES:
                errors.append(f"{kpi_id}: unresolved verification status {verification}")
                continue
            if not proof or proof.upper() in {"N/A", "TODO"}:
                errors.append(f"{kpi_id}: missing SQL proof reference")
                continue

            vtype = validation_type or ("numeric_tolerance" if schema.startswith("legacy") else "")
            if schema == "expanded" and not vtype:
                errors.append(f"{kpi_id}: missing validation_type")
                continue
            if vtype and vtype not in KNOWN_VALIDATION_TYPES:
                errors.append(f"{kpi_id}: unknown validation_type {vtype!r}")
                continue
            if schema.startswith("legacy") and not validation_type:
                warnings.append(f"{kpi_id}: legacy row missing validation_type — migration warning")

            require_vtype_in_proof = schema == "expanded"
            proof_ok = proof_hard_check(
                root,
                kpi_id,
                proof,
                errors,
                expected_kpi_id=kpi_id if schema == "expanded" else None,
                require_validation_type=require_vtype_in_proof,
                require_tolerance=vtype in {"numeric_tolerance", "ratio_tolerance"} and schema == "expanded",
            )
            if not expected or not actual:
                errors.append(f"{kpi_id}: missing expected or actual result")
                continue

            reconciled = False
            waiver_disclosures: list[Any] = []
            fingerprint = cell(row, "contract_fingerprint", "fingerprint") or compute_contract_fingerprint(row)

            def _waiver_covers_fail(
                *,
                vtype_local: str = "",
                calc_diff: Any = None,
                tol_local: str = "",
            ) -> bool:
                waiver, werrs, disposition = find_valid_waiver_for_kpi(
                    root,
                    kpi_id,
                    fingerprint=fingerprint,
                    validation_type=vtype_local or vtype,
                    calculated_status="FAIL",
                    calculated_difference=calc_diff,
                    tolerance=tol_local or tolerance or "0",
                )
                if waiver and disposition == "APPROVED_WAIVER":
                    entry = {
                        "kpi_id": kpi_id,
                        "waiver_id": waiver.waiver_id,
                        "calculated_status": "FAIL",
                        "governance_disposition": "APPROVED_WAIVER",
                        "validation_type": vtype_local or vtype,
                        "calculated_difference": str(calc_diff) if calc_diff is not None else "",
                        "tolerance": tol_local or tolerance or "0",
                        "fingerprint": fingerprint,
                    }
                    msg = (
                        f"{kpi_id}: calculated_status=FAIL governance_disposition=APPROVED_WAIVER "
                        f"(waiver_id={waiver.waiver_id})"
                    )
                    warnings.append(msg)
                    waiver_disclosures.append(entry)
                    return True
                errors.extend(werrs or [f"{kpi_id}: reconciliation FAIL/WARN without valid waiver"])
                return False

            if vtype == "set_match":
                rules = cell(row, "normalization_rules", "set_rules", "diff_/_tolerance", "tolerance")
                set_result = reconcile_set_match(expected, actual, rules)
                calc = set_result["calculated_status"]
                if set_result.get("duplicate_members"):
                    warnings.append(
                        f"{kpi_id}: set_match duplicate members {set_result['duplicate_members']}"
                    )
                if verification == "PASS" and calc == "FAIL":
                    errors.append(
                        f"{kpi_id}: recorded Verification PASS contradicts set_match "
                        f"(missing={sorted(set_result['missing'])}, "
                        f"unexpected={sorted(set_result['unexpected'])})"
                    )
                elif calc == "PASS":
                    reconciled = True
                elif calc == "FAIL":
                    reconciled = _waiver_covers_fail(vtype_local="set_match")
                elif verification == "WARN":
                    reconciled = _waiver_covers_fail(vtype_local="set_match")
            elif vtype == "row_count_match":
                rc = reconcile_row_count(expected, actual, tolerance)
                if rc["errors"]:
                    errors.append(f"{kpi_id}: {'; '.join(rc['errors'])}")
                elif verification == "PASS" and rc["calculated_status"] == "FAIL":
                    errors.append(
                        f"{kpi_id}: recorded PASS contradicts row_count_match "
                        f"(expected={expected!r}, actual={actual!r}, abs_diff={rc['abs_diff']})"
                    )
                elif rc["calculated_status"] == "PASS":
                    reconciled = True
                else:
                    reconciled = _waiver_covers_fail(
                        vtype_local="row_count_match",
                        calc_diff=rc.get("abs_diff"),
                        tol_local=tolerance or "0",
                    )
            elif vtype == "acceptance_rule":
                rule_result = evaluate_typed_acceptance_rule(root, row)
                if rule_result["calculated_status"] == "FAIL":
                    errors.append(
                        f"{kpi_id}: acceptance_rule failed: {'; '.join(rule_result['errors'])}"
                    )
                else:
                    reconciled = True
            elif vtype in NUMERIC_TYPES or (
                not vtype and parse_number(expected) is not None
            ):
                reconciled = numeric_reconcile_row(
                    kpi_id,
                    expected,
                    actual,
                    tolerance or ("exact" if vtype == "numeric_exact" else "0"),
                    verification,
                    recorded_diff,
                    errors,
                    warnings,
                    validation_type=vtype or "numeric_tolerance",
                    root=root,
                    fingerprint=fingerprint,
                    waiver_disclosures=waiver_disclosures,
                )
            elif vtype in {"blocked", "deferred"}:
                reason = cell(row, "reason", "caveats")
                if not reason:
                    errors.append(f"{kpi_id}: {vtype} validation requires reason")
                reconciled = verification in {"WARN", "FAIL", "BLOCKED", "DEFERRED"}
            else:
                errors.append(f"{kpi_id}: unknown validation_type {vtype!r}")

            # Technical PASS must never be treated as business APPROVED here
            if verification == "PASS" and approval in {"PENDING_REVIEW", "NOT_REQUESTED"}:
                warnings.append(
                    f"{kpi_id}: technical PASS with business approval {approval} "
                    "(not trusted for production)"
                )

            # Governed waiver counts toward coverage; calculated FAIL remains disclosed
            if reconciled and proof_ok:
                critical_reconciled += 1
            for item in waiver_disclosures:
                if isinstance(item, dict):
                    governed_exceptions.append(item)

        elif verification in {"PASS", "WARN"}:
            if proof:
                proof_hard_check(root, kpi_id, proof, errors)

    matrix_ok = 0
    matrix_critical = 0
    for index, row in enumerate(matrix, start=1):
        metric_id = cell(row, "metric", "metric_id", "id", "kpi") or f"Metric row {index}"
        status = cell(
            row,
            "recorded_technical_status",
            "status",
            "verification_status",
            "calculated_status",
        ).upper()
        source_proof = cell(row, "source_proof")
        mart_proof = cell(row, "current_model_proof", "mart_proof", "current_proof")
        expected = cell(row, "expected_result", "expected")
        actual = cell(row, "actual_result", "actual")
        tolerance = cell(row, "tolerance", "diff", "diff_tolerance")
        vtype = cell(row, "validation_type").lower()

        # Layer applicability
        for layer_alias, layer_name in (
            ("semantic_proof", "semantic_proof"),
            ("presentation_proof", "presentation_proof"),
        ):
            layer_val = cell(row, layer_alias)
            if not layer_val:
                continue
            upper = layer_val.upper()
            if upper in {"SUPPORTED", "BLOCKED", "DEFERRED"}:
                continue
            if upper.startswith("NOT_APPLICABLE"):
                continue
            if upper in {"N/A", "NA", "NONE"}:
                errors.append(
                    f"{metric_id}: {layer_name} needs NOT_APPLICABLE: <reason>, SUPPORTED, BLOCKED, or DEFERRED"
                )

        if status in {"DEFERRED", "SKIPPED"}:
            continue
        if status in BAD_STATUSES:
            errors.append(f"{metric_id}: unresolved status {status}")
            continue
        matrix_critical += 1
        if status not in VALID_STATUSES:
            errors.append(f"{metric_id}: invalid or missing status '{status}'")
            continue
        if not source_proof or source_proof.upper() in {"N/A", "TODO"}:
            # Allow explicit NOT_APPLICABLE with reason
            if not str(source_proof).upper().startswith("NOT_APPLICABLE"):
                errors.append(f"{metric_id}: missing source proof")
                continue
        if not mart_proof or mart_proof.upper() in {"N/A", "TODO"}:
            if not str(mart_proof).upper().startswith("NOT_APPLICABLE"):
                errors.append(f"{metric_id}: missing mart proof")
                continue
        if source_proof and not str(source_proof).upper().startswith("NOT_APPLICABLE"):
            proof_hard_check(root, f"{metric_id} source", source_proof, errors)
        if mart_proof and not str(mart_proof).upper().startswith("NOT_APPLICABLE"):
            proof_hard_check(root, f"{metric_id} mart", mart_proof, errors)
        if not expected or not actual:
            errors.append(f"{metric_id}: missing expected or actual result")
            continue
        if vtype == "set_match":
            set_result = reconcile_set_match(expected, actual, tolerance)
            if status == "PASS" and set_result["calculated_status"] == "FAIL":
                errors.append(f"{metric_id}: matrix set_match PASS contradicts calculation")
            elif set_result["calculated_status"] == "PASS":
                matrix_ok += 1
        elif numeric_reconcile_row(
            metric_id, expected, actual, tolerance or "0", status, "", errors, warnings
        ):
            matrix_ok += 1

    cov = ratio(critical_reconciled, critical_total)
    print("Metric reconciliation summary:")
    print(f"  KPI contract schema: {schema}")
    print(f"  KPI contracts checked: {len(contracts)}")
    print(f"  metric matrix rows checked: {len(matrix)}")
    print(f"  blocked/deferred KPIs: {blocked_or_deferred}")
    if cov is None:
        print("  critical reconciliation coverage: N/A (no APPROVED/PROPOSED KPIs)")
        if contracts:
            # Empty denominator is not 100%
            errors.append("no APPROVED/PROPOSED KPIs to reconcile (empty set is not 100%)")
    else:
        print(f"  critical reconciliation coverage: {critical_reconciled}/{critical_total} ({cov:.0%})")
        if cov < recon_required:
            errors.append(
                f"critical reconciliation coverage {cov:.0%} below required {recon_required:.0%}"
            )
    if matrix_critical:
        print(f"  matrix reconciled: {matrix_ok}/{matrix_critical}")

    return print_results(
        "Metric reconciliation",
        errors,
        warnings,
        output_json=getattr(args, "output_json", None),
        validator_id=Path(__file__).stem,
        details={"governed_exceptions": governed_exceptions},
    )


if __name__ == "__main__":
    raise SystemExit(main())
