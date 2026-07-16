#!/usr/bin/env python3
"""Check per-fact analytical coverage contracts.

Maps each detected gold fact/event model to an exact contract row and requires
applicable analytical families to be evaluated with explicit applicability tokens.
Overall row Status is read only via named_status (never from analytical columns).

The analytical status-family field must NOT use generic `status` as an alias.
Use status_distribution / status_mix / workflow_state_analysis only.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from lib_gate_common import (
    add_output_json_arg,
    cell,
    list_analytical_facts,
    list_gold_fact_names,
    load_analytics_policy,
    named_status,
    normalize_header,
    parse_markdown_tables,
    print_results,
    ratio,
    read_text,
    table_dicts,
)

# Descriptive fields: nonempty business text (not applicability tokens alone).
REQUIRED_DESCRIPTIVE_FIELDS = (
    ("grain", ("grain",)),
    ("counting_key", ("counting_key", "counting key", "count_key")),
    ("primary_date", ("primary_date", "primary date")),
    ("business_questions", ("business_questions", "business questions")),
    ("unsupported_opportunities", ("unsupported_opportunities", "unsupported opportunities")),
    ("approval", ("approval", "approval_status")),
)

# Applicability fields: must be SUPPORTED | NOT_APPLICABLE | BLOCKED | DEFERRED.
# Generic "status" is intentionally excluded from status_distribution aliases.
REQUIRED_APPLICABILITY_FIELDS = (
    ("secondary_date_roles", ("secondary_date_roles", "secondary date roles", "secondary_dates")),
    ("volume", ("volume",)),
    ("distinct_entity_volume", ("distinct_entity_volume", "distinct entity volume", "distinct_volume")),
    ("amount", ("amount", "amount_or_quantity", "amount or quantity", "value")),
    ("quantity", ("quantity", "amount_or_quantity", "amount or quantity")),
    ("duration", ("duration", "duration_or_balance", "duration or balance")),
    ("balance", ("balance", "duration_or_balance", "duration or balance")),
    ("min_max_date", ("min_max_date", "minimum/maximum date", "min/max date", "date_coverage")),
    (
        "status_distribution",
        ("status_distribution", "status distribution", "status_mix", "workflow_state_analysis"),
    ),
    ("lifecycle", ("lifecycle",)),
    ("dimensions", ("dimensions", "dimension", "segmentation")),
    ("time_trends", ("time_trends", "time trends", "time", "time_intelligence")),
    ("period_comparison", ("period_comparison", "period comparison", "period compare")),
    ("quality", ("quality", "data_quality", "data quality")),
    ("exceptions", ("exceptions", "exception")),
    ("aging", ("aging",)),
    ("reconciliation", ("reconciliation", "reconcile")),
)

# Compact fixture schema (combined columns) — still accepted during migration.
COMPACT_APPLICABILITY_FIELDS = (
    ("volume", ("volume",)),
    ("amount_or_quantity", ("amount_or_quantity", "amount or quantity", "amount", "quantity", "value")),
    ("duration_or_balance", ("duration_or_balance", "duration or balance", "duration", "balance")),
    (
        "status_distribution",
        ("status_distribution", "status distribution", "status_mix", "workflow_state_analysis"),
    ),
    ("lifecycle", ("lifecycle",)),
    ("dimensions", ("dimensions", "dimension", "segmentation")),
    ("time_trends", ("time_trends", "time trends", "time", "time_intelligence", "date_coverage")),
    ("period_comparison", ("period_comparison", "period comparison", "period compare")),
    ("quality", ("quality", "data_quality", "data quality")),
    ("exceptions", ("exceptions", "exception")),
    ("aging", ("aging",)),
    ("reconciliation", ("reconciliation", "reconcile")),
)

APPLICABILITY_SUPPORTED = frozenset({"SUPPORTED", "PASS"})
APPLICABILITY_NA = frozenset({"NOT_APPLICABLE", "N/A", "NA"})


def normalize_applicability(raw: str) -> str:
    token = raw.strip().upper().replace("-", "_").replace(" ", "_")
    if token in APPLICABILITY_SUPPORTED:
        return "SUPPORTED"
    if token in APPLICABILITY_NA:
        return "NOT_APPLICABLE"
    if token == "BLOCKED":
        return "BLOCKED"
    if token == "DEFERRED":
        return "DEFERRED"
    return "UNKNOWN"


def _legacy_field_value(row: dict[str, str], label: str, aliases: tuple[str, ...]) -> str:
    value = cell(row, *aliases)
    if value:
        return value
    legacy_map = {
        "amount": ("value", "amount_or_quantity"),
        "quantity": ("amount_or_quantity",),
        "duration": ("duration_or_balance",),
        "balance": ("duration_or_balance",),
        "time_trends": ("time",),
        "quality": ("data_quality",),
        "min_max_date": ("date_coverage", "time"),
    }
    for legacy_alias in legacy_map.get(label, ()):
        legacy_val = row.get(normalize_header(legacy_alias), "")
        if legacy_val:
            return legacy_val
    return ""


def uses_expanded_schema(row: dict[str, str]) -> bool:
    markers = (
        "distinct_entity_volume",
        "secondary_date_roles",
        "min_max_date",
        "unsupported_opportunities",
    )
    return any(normalize_header(m) in row and row[normalize_header(m)] for m in markers) or (
        "amount" in row and "quantity" in row
    )


def is_legacy_fact_row(row: dict[str, str]) -> bool:
    if uses_expanded_schema(row):
        return False
    expanded_markers = (
        "lifecycle",
        "period_comparison",
        "primary_date",
        "amount_or_quantity",
        "status_distribution",
    )
    if any(cell(row, marker) for marker in expanded_markers):
        return False
    return bool(cell(row, "value") or cell(row, "time") or cell(row, "quality"))


def fact_coverage_rows(path: Path) -> list[dict[str, str]]:
    """Parse fact coverage tables.

    When two Status columns exist (legacy), first maps to status_distribution and
    last remains overall Status. A single Status column is overall Status only —
    it must never satisfy status_distribution.
    """
    rows: list[dict[str, str]] = []
    for headers, data in parse_markdown_tables(read_text(path)):
        norm_headers = [normalize_header(h) for h in headers]
        status_indices = [idx for idx, header in enumerate(norm_headers) if header == "status"]
        has_status_distribution = "status_distribution" in norm_headers
        is_legacy_dup_status = (not has_status_distribution) and len(status_indices) >= 2

        for cells in data:
            if not cells or cells[0].upper() == "TODO":
                continue
            row = {
                norm_headers[idx]: (cells[idx].strip() if idx < len(cells) else "")
                for idx in range(len(norm_headers))
                if norm_headers[idx]
            }
            if is_legacy_dup_status:
                first_idx, last_idx = status_indices[0], status_indices[-1]
                row["status_distribution"] = (
                    cells[first_idx].strip() if first_idx < len(cells) else ""
                )
                row["status"] = cells[last_idx].strip() if last_idx < len(cells) else row.get("status", "")
            rows.append(row)
    if rows:
        return rows
    return table_dicts(path, required_any_headers=("fact", "fact_model", "model", "name", "status"))


def validate_applicability(
    fact_name: str,
    field_label: str,
    raw_value: str,
    row: dict[str, str],
    errors: list[str],
) -> bool:
    if not raw_value or raw_value.strip().upper() in {"TODO", "TBD"}:
        errors.append(f"{fact_name}: missing applicability for {field_label}")
        return False

    # Bare N/A / NA / NONE / NOT_APPLICABLE without a reason fails
    bare = raw_value.strip().upper().replace("-", "_").replace(" ", "_")
    if bare in {"N/A", "NA", "NONE", "NOT_APPLICABLE"}:
        errors.append(
            f"{fact_name}: {field_label} bare {raw_value!r} without reason — "
            "use NOT_APPLICABLE: <specific reason>"
        )
        return False

    # Allow "NOT_APPLICABLE: reason" / "SUPPORTED: proof" forms
    if ":" in raw_value:
        prefix, _, remainder = raw_value.partition(":")
        norm = normalize_applicability(prefix)
        inline_reason = remainder.strip()
    else:
        norm = normalize_applicability(raw_value)
        inline_reason = ""

    if norm == "UNKNOWN":
        errors.append(
            f"{fact_name}: {field_label} requires SUPPORTED|NOT_APPLICABLE|BLOCKED|DEFERRED, got {raw_value!r}"
        )
        return False

    notes = cell(row, "notes", "reason", "comment") or inline_reason
    owner = cell(row, "owner")
    next_action = cell(row, "next_action", "next action", "recommended_action")
    missing_evidence = cell(row, "missing_evidence", "missing evidence")
    review_condition = cell(
        row,
        "review_condition",
        "review condition",
        "reassessment_condition",
        "reassessment condition",
    )
    # Family-specific evidence: prefer inline after colon, then field itself if SUPPORTED: proof,
    # then dedicated proof columns — NOT a shared Notes column alone for SUPPORTED.
    family_evidence = inline_reason if norm == "SUPPORTED" and inline_reason else ""
    if not family_evidence and norm == "SUPPORTED" and ":" not in raw_value:
        # Value is just SUPPORTED — require dedicated proof/evidence column (not Notes alone)
        family_evidence = cell(row, "proof", "evidence", "sql_proof")
    evidence = family_evidence or inline_reason

    if norm == "SUPPORTED":
        if not evidence:
            errors.append(f"{fact_name}: {field_label} SUPPORTED requires family-specific proof/reference")
            return False
        # Reject Notes-only generic evidence marker
        if evidence.strip().lower() in {"see notes", "notes", "generic", "same as above"}:
            errors.append(
                f"{fact_name}: {field_label} SUPPORTED requires family-specific proof, not generic Notes"
            )
            return False
        return True

    if norm == "NOT_APPLICABLE":
        if not notes:
            errors.append(f"{fact_name}: {field_label} NOT_APPLICABLE requires a reason")
            return False
        return True

    if norm == "BLOCKED":
        missing = []
        if not notes:
            missing.append("reason")
        if not owner:
            missing.append("owner")
        if not missing_evidence:
            missing.append("missing_evidence")
        if not next_action:
            missing.append("next_action")
        if missing:
            errors.append(
                f"{fact_name}: {field_label} BLOCKED requires reason, owner, "
                f"missing_evidence, and next_action (missing: {', '.join(missing)})"
            )
            return False
        return True

    if norm == "DEFERRED":
        missing = []
        if not notes:
            missing.append("reason")
        if not owner:
            missing.append("owner")
        if not next_action:
            missing.append("next_action")
        if not review_condition:
            missing.append("review_condition")
        if missing:
            errors.append(
                f"{fact_name}: {field_label} DEFERRED requires reason, owner, "
                f"next_action, and review_condition (missing: {', '.join(missing)})"
            )
            return False
        return True

    return False


def row_analytical_complete(fact_name: str, row: dict[str, str], errors: list[str]) -> bool:
    ok = True
    legacy = is_legacy_fact_row(row)
    expanded = uses_expanded_schema(row)

    if expanded:
        descriptive_fields = REQUIRED_DESCRIPTIVE_FIELDS
    elif legacy:
        descriptive_fields = tuple(
            (label, aliases)
            for label, aliases in REQUIRED_DESCRIPTIVE_FIELDS
            if label not in {"primary_date", "unsupported_opportunities", "approval"}
        )
    else:
        # Compact modern fixtures (combined amount/quantity columns)
        descriptive_fields = tuple(
            (label, aliases)
            for label, aliases in REQUIRED_DESCRIPTIVE_FIELDS
            if label not in {"unsupported_opportunities", "approval"}
        )

    for label, aliases in descriptive_fields:
        value = _legacy_field_value(row, label, aliases)
        if not value or value.strip().upper() in {"TODO", "TBD"}:
            errors.append(f"{fact_name}: missing descriptive value for {label}")
            ok = False

    if expanded:
        applicability_fields = REQUIRED_APPLICABILITY_FIELDS
    elif legacy:
        applicability_fields = tuple(
            (label, aliases)
            for label, aliases in COMPACT_APPLICABILITY_FIELDS
            if label
            not in {
                "duration_or_balance",
                "lifecycle",
                "period_comparison",
                "exceptions",
                "aging",
            }
        )
    else:
        applicability_fields = COMPACT_APPLICABILITY_FIELDS

    for label, aliases in applicability_fields:
        value = _legacy_field_value(row, label, aliases)
        if not validate_applicability(fact_name, label, value, row, errors):
            ok = False

    # One generic proof/reference reused for every SUPPORTED family fails
    supported_proofs: list[str] = []
    for label, aliases in applicability_fields:
        value = _legacy_field_value(row, label, aliases)
        if not value:
            continue
        if ":" in value and normalize_applicability(value.split(":", 1)[0]) == "SUPPORTED":
            supported_proofs.append(value.split(":", 1)[1].strip().lower())
        elif normalize_applicability(value) == "SUPPORTED":
            supported_proofs.append(cell(row, "proof", "evidence", "sql_proof", "notes").strip().lower())
    supported_proofs = [p for p in supported_proofs if p]
    if len(supported_proofs) >= 3 and len(set(supported_proofs)) == 1:
        errors.append(
            f"{fact_name}: one generic proof reused for all analytical families "
            f"({supported_proofs[0]!r}) — each SUPPORTED family needs family-specific evidence"
        )
        ok = False
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_output_json_arg(parser)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    policy = load_analytics_policy(root)
    required = float(policy.get("critical_fact_coverage_required", 1.0))

    insights = root / "reports" / "agent" / "09_analytics_insights"
    contracts = insights / "fact_coverage_contracts.md"
    gold_facts = list_gold_fact_names(root)

    if not insights.exists():
        return print_results(
            "Fact analytical coverage check",
            [],
            [],
            output_json=getattr(args, "output_json", None),
            validator_id=Path(__file__).stem,
            skipped=True,
            skip_reason="no analytics insight folder",
        )
    if not gold_facts and not contracts.exists():
        return print_results(
            "Fact analytical coverage check",
            [],
            [],
            output_json=getattr(args, "output_json", None),
            validator_id=Path(__file__).stem,
            skipped=True,
            skip_reason="no gold facts / fact contracts yet",
        )

    errors: list[str] = []
    warnings: list[str] = []

    if not contracts.exists():
        errors.append("missing reports/agent/09_analytics_insights/fact_coverage_contracts.md")
        return print_results("Fact analytical coverage check", errors, warnings, output_json=getattr(args, "output_json", None), validator_id=Path(__file__).stem)

    rows = fact_coverage_rows(contracts)
    by_fact: dict[str, dict[str, str]] = {}
    by_unique_id: dict[str, dict[str, str]] = {}
    for row in rows:
        name = cell(row, "fact", "fact_model", "model", "name", "resource_name").lower().replace("`", "")
        unique_id = cell(row, "unique_id", "fact_id", "unique id")
        if unique_id:
            by_unique_id[unique_id] = row
        if name:
            by_fact[name] = row

    analytical_facts = [item for item in list_analytical_facts(root) if item.get("ambiguous") != "true"]
    for item in list_analytical_facts(root):
        if item.get("ambiguous") == "true":
            errors.append(
                f"fact name {item.get('name')}: ambiguous across packages/resources — "
                "require unique_id in fact_catalog / contracts"
            )

    gold_facts = list_gold_fact_names(root)
    print(
        f"Fact coverage contracts: rows={len(by_fact)}, gold_facts={len(gold_facts)}, "
        f"unique_ids={len(analytical_facts)}"
    )

    if analytical_facts:
        missing_uids = [
            f"{item.get('unique_id')} ({item.get('name')})"
            for item in analytical_facts
            if item.get("unique_id") not in by_unique_id
            and (item.get("name") or "").lower() not in by_fact
        ]
        if missing_uids:
            errors.append(
                "fact_coverage_contracts missing rows for facts: " + ", ".join(missing_uids[:12])
            )
        for name, row in by_fact.items():
            if cell(row, "unique_id", "fact_id"):
                continue
            matches = [f for f in analytical_facts if f.get("name") == name]
            if len(matches) > 1:
                errors.append(
                    f"{name}: fact contract name maps to multiple unique_ids — "
                    + ", ".join(m.get("unique_id", "") for m in matches)
                )
    elif gold_facts:
        missing = [f for f in gold_facts if f not in by_fact]
        if missing:
            errors.append(
                "fact_coverage_contracts missing rows for gold facts: " + ", ".join(missing)
            )
        extra = [
            f
            for f in by_fact
            if f not in gold_facts and (f.startswith("fct_") or f.startswith("mart_"))
        ]
        if extra:
            warnings.append(
                "contract rows without matching gold SQL model: " + ", ".join(sorted(extra))
            )

    complete = 0
    applicable = 0
    if analytical_facts:
        for item in analytical_facts:
            fact_name = item.get("name") or ""
            row = by_unique_id.get(item.get("unique_id") or "") or by_fact.get(fact_name or "")
            if not row:
                continue
            applicable += 1
            label = item.get("unique_id") or fact_name
            status = named_status(row)
            if status == "UNKNOWN":
                errors.append(f"{label}: missing explicit Status column value")
                continue
            if status == "FAIL":
                errors.append(f"{label}: fact coverage Status is FAIL/BLOCKED")
                continue
            if status == "NOT_APPLICABLE":
                applicable -= 1
                continue
            if status == "WARN":
                warnings.append(f"{label}: fact coverage Status is WARN/DEFERRED")
                continue
            if row_analytical_complete(fact_name or label, row, errors) and status == "PASS":
                complete += 1
    else:
        for fact_name in gold_facts or sorted(by_fact):
            row = by_fact.get(fact_name)
            if not row:
                continue
            applicable += 1
            status = named_status(row)
            if status == "UNKNOWN":
                errors.append(f"{fact_name}: missing explicit Status column value")
                continue
            if status == "FAIL":
                errors.append(f"{fact_name}: fact coverage Status is FAIL/BLOCKED")
                continue
            if status == "NOT_APPLICABLE":
                applicable -= 1
                continue
            if status == "WARN":
                warnings.append(f"{fact_name}: fact coverage Status is WARN/DEFERRED")
                continue
            if row_analytical_complete(fact_name, row, errors) and status == "PASS":
                complete += 1

    cov = ratio(complete, applicable)
    if cov is None:
        if gold_facts or analytical_facts:
            errors.append("no applicable fact coverage rows (empty set is NOT_APPLICABLE, not 100%)")
        else:
            warnings.append("no fact coverage rows to score yet")
    else:
        print(f"Critical fact coverage: {complete}/{applicable} ({cov:.0%})")
        if cov < required:
            errors.append(f"critical fact coverage {cov:.0%} below required {required:.0%}")

    return print_results("Fact analytical coverage check", errors, warnings, output_json=getattr(args, "output_json", None), validator_id=Path(__file__).stem)


if __name__ == "__main__":
    raise SystemExit(main())
