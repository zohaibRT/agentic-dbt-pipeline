# Metric Verification Matrix (TEST FIXTURE)

| Metric ID | Validation Type | Source Proof | Current Model Proof | Semantic Proof | Presentation Proof | Expected Result | Actual Result | Calculated Difference | Tolerance | Calculated Status | Recorded Technical Status | Business Approval Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| KPI-001 | numeric_tolerance | reports/agent/sql_proofs/010_volume.sql | reports/agent/sql_proofs/010_volume.sql | NOT_APPLICABLE: no semantic layer in fixture | DEFERRED: presentation checked separately | 100 | 100 | 0 | 0 | PASS | PASS | APPROVED | Matches |
| KPI-002 | ratio_tolerance | reports/agent/sql_proofs/020_rate.sql | reports/agent/sql_proofs/020_rate.sql | NOT_APPLICABLE: no semantic layer in fixture | DEFERRED: presentation checked separately | 0.8 | 0.8 | 0 | 0 | PASS | PASS | APPROVED | Matches |
