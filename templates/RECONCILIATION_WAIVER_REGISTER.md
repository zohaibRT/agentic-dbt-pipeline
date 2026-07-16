# Reconciliation Waiver Register

Formal waivers for calculated reconciliation failures. A calculated FAIL never
becomes technical PASS. A valid waiver yields `governance_disposition=APPROVED_WAIVER`
while preserving `calculated_status=FAIL`.

| Waiver ID | KPI ID | Validation Type | Calculated Result | Calculated Difference | Tolerance | Reason | Business Impact | Risk Owner | Approver | Approval Evidence | Approval Date | Expiry Or Review Condition | Current Status | Contract Fingerprint |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| W-EXAMPLE | kpi_example | numeric_tolerance | FAIL | 0.05 | 0.01 | Known late-arriving source lag for period close | Low — disclosed on executive report | Business Risk Owner | Named Approver | reports/agent/BUSINESS_APPROVAL_REGISTER.md | 2026-01-15 | 2027-01-15 | APPROVED | <fingerprint> |
