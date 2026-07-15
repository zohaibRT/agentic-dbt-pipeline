# Fact Coverage Contracts

Evaluate each material fact. Mark analytical-family cells with exactly one of:

`SUPPORTED` | `NOT_APPLICABLE` | `BLOCKED` | `DEFERRED`

Rules:

- **SUPPORTED** requires evidence/proof (Notes, Proof, or Evidence column).
- **NOT_APPLICABLE** requires a reason in Notes.
- **BLOCKED** requires reason, Owner, Missing Evidence, and Next Action.
- **DEFERRED** requires reason, Owner, Next Action, and Review Condition.

Do **not** use the overall **Status** column to satisfy Status Distribution.
Status Distribution aliases are only: `status_distribution`, `status_mix`, `workflow_state_analysis`.

| Fact | Grain | Counting Key | Primary Date | Secondary Date Roles | Volume | Distinct Entity Volume | Amount | Quantity | Duration | Balance | Min/Max Date | Status Distribution | Lifecycle | Dimensions | Time Trends | Period Compare | Quality | Exceptions | Aging | Reconciliation | Business Questions | Unsupported Opportunities | Approval | Owner | Missing Evidence | Next Action | Review Condition | Notes | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| <fact_model> | <grain> | <key> | <date> | NOT_APPLICABLE | SUPPORTED | NOT_APPLICABLE | SUPPORTED | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | DEFERRED | SUPPORTED | SUPPORTED | NOT_APPLICABLE | SUPPORTED | <questions> | <gaps> | APPROVED | analytics | n/a | n/a | When history exists | Proof: sql_proofs/volume.sql | PASS |
