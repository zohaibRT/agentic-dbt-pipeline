#!/usr/bin/env python3
"""Shared KPI contract + HITL artifact text for analytics/dbt fixtures."""

from __future__ import annotations

from lib_gate_common import cell, compute_contract_fingerprint, normalize_header, parse_markdown_tables


def _row_fingerprint_from_cells(cells: dict[str, str]) -> str:
    return compute_contract_fingerprint(cells)


def kpi_contracts_markdown(*, process: str, fact: str, volume_expected: str = "100") -> str:
    """Return expanded canonical KPI contract table for fixtures."""
    rate_actual = "0.8" if volume_expected == "100" else "0.4"
    # Build rows without fingerprint first, then stamp calculated fingerprints.
    draft = f"""
# Key Performance Indicator Definition Contracts (TEST FIXTURE)

Synthetic approval evidence is labelled TEST FIXTURE only — not production approval.

| KPI ID | Contract Version | Contract Fingerprint | Display Name | Metric Class | Business Process | Business Question | Decision Supported | Action When Bad | Business Owner | Approver | Business Definition | Formula | Grain | Counting Key | Source Models | Source Columns | Date Field | Date Role | Timezone | Included Records | Excluded Records | Status Logic | Dimensions | Numerator | Denominator | Unit | Currency | Format | Precision | Aggregation Behavior | Null Behavior | Zero Denominator Behavior | Refresh Frequency | Freshness SLA | Target | Target Source | Warning Threshold | Critical Threshold | Desired Direction | Validation Source | Validation Type | Reconciliation Tolerance | SQL Proof | Expected Result | Actual Result | Calculated Difference | Calculated Status | Technical Verification Status | Business Approval Status | Approval Evidence | Approval Date | Approval Conditions | Approval Expiry Or Review Condition | Confidence | Caveats | Missing Evidence | Recommended Next Action | Review Or Resolution Condition |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| KPI-001 | 1.0 | __FP1__ | Volume KPI | kpi | {process} | How many events occurred? | Capacity planning | Investigate drop | fixture-owner | fixture-approver | Total count of valid events in period | count(*) | event | event_id | {fact} | event_id,event_date,status | event_date | occurred | NOT_APPLICABLE: date-only field | all valid | test rows | exclude cancelled from volume only when flagged | status | NOT_APPLICABLE: count KPI has no numerator | NOT_APPLICABLE: count KPI has no denominator | count | NOT_APPLICABLE: nonfinancial count | integer | 0 | additive | exclude null keys | NOT_APPLICABLE: no denominator | daily | 24h | Target not defined | NOT_APPLICABLE: target not defined | NOT_APPLICABLE: no target | NOT_APPLICABLE: no target | increase | reports/agent/sql_proofs/010_volume.sql | numeric_tolerance | 0 | reports/agent/sql_proofs/010_volume.sql | {volume_expected} | {volume_expected} | 0 | PASS | PASS | APPROVED | reports/agent/BUSINESS_APPROVAL_REGISTER.md#KPI-001 | 2026-01-15 | NOT_APPLICABLE: unconditional approval | NOT_APPLICABLE: unconditional approval | HIGH | Matches source | none | none | none |
| KPI-002 | 1.0 | __FP2__ | Completion rate KPI | kpi | {process} | What share completed? | Process health | Review failures | fixture-owner | fixture-approver | Share of non-cancelled events marked completed | completed_count / event_count | event | event_id | {fact} | event_id,event_date,status | event_date | completed | NOT_APPLICABLE: date-only field | non-cancelled | cancelled | completed among non-cancelled | status | completed_count | event_count | ratio | NOT_APPLICABLE: ratio metric | percent | 2 | ratio | exclude null status | return null | daily | 24h | Target not defined | NOT_APPLICABLE: target not defined | NOT_APPLICABLE: no target | NOT_APPLICABLE: no target | increase | reports/agent/sql_proofs/020_rate.sql | ratio_tolerance | 0 | reports/agent/sql_proofs/020_rate.sql | {rate_actual} | {rate_actual} | 0 | PASS | PASS | APPROVED | reports/agent/BUSINESS_APPROVAL_REGISTER.md#KPI-002 | 2026-01-15 | NOT_APPLICABLE: unconditional approval | NOT_APPLICABLE: unconditional approval | HIGH | Definition approved | none | none | none |
"""
    rows = []
    for headers, data in parse_markdown_tables(draft):
        norm = [normalize_header(h) for h in headers]
        for cells in data:
            row = {
                norm[i]: (cells[i].strip() if i < len(cells) else "")
                for i in range(len(norm))
                if norm[i]
            }
            rows.append(row)
        break
    fp1 = _row_fingerprint_from_cells(rows[0]) if rows else "missing"
    fp2 = _row_fingerprint_from_cells(rows[1]) if len(rows) > 1 else "missing"
    return draft.replace("__FP1__", fp1).replace("__FP2__", fp2)


def approval_register_markdown(*, process: str, fact: str, volume_expected: str = "100") -> str:
    contracts = kpi_contracts_markdown(process=process, fact=fact, volume_expected=volume_expected)
    rows = []
    for headers, data in parse_markdown_tables(contracts):
        norm = [normalize_header(h) for h in headers]
        for cells in data:
            row = {
                norm[i]: (cells[i].strip() if i < len(cells) else "")
                for i in range(len(norm))
                if norm[i]
            }
            rows.append(row)
        break
    lines = [
        "# Business Approval Register (TEST FIXTURE)",
        "",
        "Synthetic approvals for automated fixtures only. Not production human approval.",
        "",
        "| Approval ID | Object Type | Object ID | Contract Version | Contract Fingerprint | Business Definition | Formula | Inclusion and Exclusion Logic | Date Role | Aggregation Behavior | Target and Threshold Status | Business Owner | Approver | Approval Status | Approval Date | Conditions | Expiry or Review Condition | Evidence Path |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        kpi = cell(row, "kpi_id")
        lines.append(
            "| BA-"
            + kpi
            + " | kpi | "
            + kpi
            + " | "
            + cell(row, "contract_version")
            + " | "
            + cell(row, "contract_fingerprint")
            + " | "
            + cell(row, "business_definition")
            + " | "
            + cell(row, "formula")
            + " | include="
            + cell(row, "included_records")
            + "; exclude="
            + cell(row, "excluded_records")
            + " | "
            + cell(row, "date_role")
            + " | "
            + cell(row, "aggregation_behavior")
            + " | target not defined | fixture-owner | fixture-approver | APPROVED | 2026-01-15 | none | none | reports/agent/DECISION_LOG.md#"
            + kpi
            + " |"
        )
    return "\n".join(lines) + "\n"


def decision_log_markdown() -> str:
    return """
# Decision Log (TEST FIXTURE)

Append-only. Do not overwrite prior decisions.

| Decision ID | Original Question | Options Considered | Machine Recommendation | Final Human Decision | Decision Owner | Approver | Date | Evidence | Affected Models | Affected Metrics | Revalidation Requirement | Previous Decision Reference | Decision Type |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DL-KPI-001 | Confirm volume KPI inclusion rules | include all valid / exclude test | exclude test rows | Accepted machine recommendation | fixture-owner | fixture-approver | 2026-01-15 | reports/agent/BUSINESS_APPROVAL_REGISTER.md#KPI-001 | fct | KPI-001 | Revalidate on formula change | none | HYBRID_DECISION |
| DL-KPI-002 | Confirm completion rate formula | completed/all / completed/non-cancelled | completed/non-cancelled | Accepted machine recommendation | fixture-owner | fixture-approver | 2026-01-15 | reports/agent/BUSINESS_APPROVAL_REGISTER.md#KPI-002 | fct | KPI-002 | Revalidate on inclusion change | none | HYBRID_DECISION |
"""


def attention_board_markdown() -> str:
    return """
# Human Attention Board (TEST FIXTURE)

| Decision ID | Decision Type | Area | Business Process | Object Type | Object ID | Question Requiring Human Input | Machine Evidence | Machine Recommendation | Alternative Options | Risk of No Decision | Proposed Owner | Due or Review Condition | Status | Final Human Decision | Approval Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| HA-NONE | MACHINE_RESOLVABLE | analytics | n/a | n/a | n/a | No open human decisions for this fixture | Fixture validators pass | Continue | n/a | none | fixture-owner | n/a | APPROVED | Continue fixture validation | reports/agent/DECISION_LOG.md |
"""


def volume_sql(*, kpi_id: str, expected: str, validation_type: str = "numeric_tolerance") -> str:
    return f"""
-- purpose: volume KPI proof for {kpi_id}
-- kpi_id: {kpi_id}
-- validation_type: {validation_type}
-- expected result: {expected}
-- captured result: {expected}
-- tolerance: 0
-- technical_verification_status: PASS
-- status: PASS
select {expected} as volume;
"""


def rate_sql(*, kpi_id: str, expected: str, validation_type: str = "ratio_tolerance") -> str:
    return f"""
-- purpose: rate KPI proof for {kpi_id}
-- kpi_id: {kpi_id}
-- validation_type: {validation_type}
-- expected result: {expected}
-- captured result: {expected}
-- tolerance: 0
-- technical_verification_status: PASS
-- status: PASS
select {expected} as rate;
"""


def matrix_markdown(*, volume_expected: str = "100") -> str:
    rate = "0.8" if volume_expected == "100" else "0.4"
    return f"""
# Metric Verification Matrix (TEST FIXTURE)

| Metric ID | Validation Type | Source Proof | Current Model Proof | Semantic Proof | Presentation Proof | Expected Result | Actual Result | Calculated Difference | Tolerance | Calculated Status | Recorded Technical Status | Business Approval Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| KPI-001 | numeric_tolerance | reports/agent/sql_proofs/010_volume.sql | reports/agent/sql_proofs/010_volume.sql | NOT_APPLICABLE: no semantic layer in fixture | DEFERRED: presentation checked separately | {volume_expected} | {volume_expected} | 0 | 0 | PASS | PASS | APPROVED | Matches |
| KPI-002 | ratio_tolerance | reports/agent/sql_proofs/020_rate.sql | reports/agent/sql_proofs/020_rate.sql | NOT_APPLICABLE: no semantic layer in fixture | DEFERRED: presentation checked separately | {rate} | {rate} | 0 | 0 | PASS | PASS | APPROVED | Matches |
"""
