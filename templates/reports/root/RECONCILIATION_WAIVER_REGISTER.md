# Reconciliation Waiver Register

Formal human-approved exceptions for calculated reconciliation failures.

A calculated FAIL never becomes technical PASS. A valid waiver yields
`governance_disposition=APPROVED_WAIVER` (or `APPROVED_WITH_CONDITIONS`) while
preserving `calculated_status=FAIL`.

| Waiver ID | Object Type | Object ID | Validation Type | Calculated Status | Calculated Difference | Tolerance | Reason | Business Impact | Risk Owner | Approver | Approval Evidence | Approval Date | Expiry or Review Condition | Reconciliation Fingerprint | Governance Disposition | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| W-EXAMPLE | kpi | kpi_example | numeric_tolerance | FAIL | 0.05 | 0.01 | Known late-arriving source lag at period close | Low — disclosed on trusted report | Named Risk Owner | Named Approver | reports/agent/BUSINESS_APPROVAL_REGISTER.md | 2026-01-15 | 2027-01-15 | <fingerprint> | APPROVED_WAIVER | APPROVED |

## Rules

- Outside fixtures, agent-generated or synthetic approval is invalid.
- SQL PASS / dbt success is not waiver approval.
- A plain WARN row is not a waiver.
- Trusted/executive reports must disclose governed exceptions.
