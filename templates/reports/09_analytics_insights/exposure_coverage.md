# Exposure Coverage

Document downstream consumers backed by real dbt exposures when a dbt project exists. Prefer manifest `unique_id`. Types follow dbt-compatible values (dashboard, notebook, analysis, ml, application, and related); do not require a single consumer type.

Technical validation and business approval are separate. Agents must not self-approve production publication.

| Exposure ID | Unique ID | Exposure | Type | Owner | Approver | Dependent Models | Dependent Sources | Dependent Metrics | URL / Delivery | Refresh Expectation | Business Purpose | Audience | Criticality | Technical Validation Status | Business Approval Status | Approval Evidence | Exposure Fingerprint | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EXP-<name> | exposure.package.name | <name> | dashboard / notebook / analysis / ml / application / api / other | <owner> | <approver> | <unique_ids or refs> | <sources> | <metrics> | <url> | <cadence/SLA> | <purpose> | <audience> | high/medium/low | PASS/WARN/FAIL/BLOCKED/DEFERRED | NOT_REQUESTED/PENDING_REVIEW/APPROVED/... | <evidence> | <fingerprint> | PASS/WARN/BLOCKED/DEFERRED |

Documentation-only rows do not satisfy final production coverage when a dbt project and presentation exist. Fingerprint changes stale prior business approval.
