# KPI Contract and Human Approval Migration

## Why this migration exists

Production analytics requires three separated concerns:

1. Machine-discovered evidence and technical verification
2. Machine recommendation
3. Human business decision and approval

Technical PASS must never become business APPROVED automatically.

## Supported legacy headers

Legacy contracts may use shorter headers such as:

- `Owner` (maps to business_owner; approver still required for trusted approval)
- `Approval` / `Approval Status` (maps to business_approval_status)
- `Verification` / `Verification Status` (maps to technical_verification_status)
- `Expected` / `Actual` / `Diff / Tolerance`
- `Included Rows` / `Excluded Rows`
- `Unit/Currency` (unit only; currency is separate when format is currency)

Legacy schemas are detected explicitly and emit migration warnings. They do **not** bypass SQL proof checks.

## Deprecated fields / behaviors

- Using one generic `Status` for both technical and business outcomes
- Treating `formula` as `business_definition`
- Treating bare `N/A` / `NA` / `none` as applicability without a reason
- Treating agent-written `APPROVED` text as human evidence
- Treating SQL/dbt PASS as business approval

## Required new fields (expanded schema)

See `templates/reports/root/KPI_DEFINITION_CONTRACTS.md` for the full canonical table.

Critical new governance fields:

- `contract_version`, `contract_fingerprint`
- `business_definition` (separate from `formula`)
- `business_owner`, `approver`
- `technical_verification_status`, `business_approval_status`
- `approval_evidence`, `approval_date`
- `validation_type`
- `approval_conditions`, `approval_expiry_or_review_condition` (conditional approvals)

## Human approval migration behavior

1. Legacy `APPROVED` without evidence path → `PENDING_REVIEW`
2. Fingerprint change on business-significant fields → stale approval → `PENDING_REVIEW` + Human Attention Board item
3. Cosmetic display-name/spelling changes do not change the fingerprint
4. Final phase fails when production KPIs lack named owner, approver, evidence, and date
5. Warning acceptance files cannot bypass human approval

## Artifacts to create

- `reports/agent/BUSINESS_APPROVAL_REGISTER.md`
- `reports/agent/DECISION_LOG.md`
- Updated `reports/agent/HUMAN_ATTENTION_BOARD.md`
- Updated `reports/agent/HUMAN_VERIFICATION_GUIDE.md`

## Validator

`scripts/check_human_approval_coverage.py --root <project> --phase analytics|presentation|final`
