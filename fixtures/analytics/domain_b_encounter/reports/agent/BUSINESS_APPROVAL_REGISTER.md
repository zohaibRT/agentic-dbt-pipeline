# Business Approval Register (TEST FIXTURE)

Synthetic approvals for automated fixtures only. Not production human approval.

| Approval ID | Object Type | Object ID | Contract Version | Contract Fingerprint | Business Definition | Formula | Inclusion and Exclusion Logic | Date Role | Aggregation Behavior | Target and Threshold Status | Business Owner | Approver | Approval Status | Approval Date | Conditions | Expiry or Review Condition | Evidence Path |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BA-KPI-001 | kpi | KPI-001 | 1.0 | 66f9f6b243cc226e | Total count of valid events in period | count(*) | include=all valid; exclude=test rows | occurred | additive | target not defined | fixture-owner | fixture-approver | APPROVED | 2026-01-15 | none | none | reports/agent/DECISION_LOG.md#KPI-001 |
| BA-KPI-002 | kpi | KPI-002 | 1.0 | 4a654609a329fab5 | Share of non-cancelled events marked completed | completed_count / event_count | include=non-cancelled; exclude=cancelled | completed | ratio | target not defined | fixture-owner | fixture-approver | APPROVED | 2026-01-15 | none | none | reports/agent/DECISION_LOG.md#KPI-002 |
