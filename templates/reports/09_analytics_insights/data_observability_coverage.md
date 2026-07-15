# Data Observability Coverage

Domain-neutral, vendor-neutral observability checklist. Do **not** require any specific
vendor product. Accept proven evidence from structured coverage rows, dbt tests/artifacts,
SQL proofs, pipeline telemetry, monitoring integrations, or approved custom checks.

Every required domain needs an explicit **Status**.
Use **NOT_APPLICABLE** only with Notes/reason, owner, and reassessment_condition when possible.
**SUPPORTED** counts as PASS.

| Domain | Scope | Models | Metric IDs | Business Or Engineering Question | Validation Method | Proof Or Telemetry | Threshold Or SLA | Expected Result | Actual Result | Owner | Incident Or Action | Status | Notes | Reassessment Condition |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| completeness | grain keys | <models> | null_key_rate | Are required keys present? | dbt tests | test results | 0 null keys | PASS | PASS | analytics | none | PASS | Example row | n/a |
| uniqueness | grain | <models> | n/a | Is grain unique? | unique test | test log | 0 duplicates | PASS | PASS | analytics | none | PASS | Example row | n/a |
| validity | coded fields | <models> | n/a | Are values in accepted sets? | accepted_values | test log | 100% valid | PASS | PASS | analytics | none | PASS | Example row | n/a |
| consistency | cross-source | n/a | n/a | Do sources agree? | cross-check | notes | n/a | n/a | n/a | analytics | none | NOT_APPLICABLE | No second source in scope | When second source added |
| referential integrity | relationships | <models> | orphan_rate | Are FK relationships intact? | relationship tests | orphan proof | 0 orphans | PASS | PASS | analytics | none | PASS | Example row | n/a |
| reconciliation accuracy | source-to-mart | <models> | volume_kpi | Does mart match source? | variance proof | sql proof | within tolerance | PASS | PASS | analytics | none | PASS | Example row | n/a |
| freshness | source load | n/a | n/a | Is data fresh enough? | SLA note | pipeline log | daily | n/a | n/a | analytics | none | NOT_APPLICABLE | Warehouse not connected in dev | When warehouse connected |
| timeliness | pipeline duration | n/a | build_success_rate | Did pipeline finish on time? | duration notes | run log | within SLA | PASS | PASS | analytics | none | PASS | Example row | n/a |
| row-count stability | volume drift | <fact> | volume_kpi | Is volume stable? | drift monitor | volume proof | within tolerance | PASS | PASS | analytics | none | PASS | Example row | n/a |
| distribution stability | status mix | <fact> | n/a | Is status mix stable? | mix monitor | status proof | within tolerance | PASS | PASS | analytics | none | PASS | Example row | n/a |
| pipeline reliability | build health | n/a | build_success_rate | Are builds reliable? | build monitor | CI log | 100% success | PASS | PASS | analytics | none | PASS | Example row | n/a |
| test reliability | dbt tests | n/a | failed_test_count | Are tests reliable? | test monitor | test log | 0 failures | PASS | PASS | analytics | none | PASS | Example row | n/a |
| documentation coverage | model docs | all models | n/a | Are models documented? | docs check | manifest | 100% documented | PASS | PASS | analytics | none | PASS | Example row | n/a |
| model ownership coverage | owners | all models | n/a | Are owners assigned? | owner audit | contracts | all owned | PASS | PASS | analytics | none | PASS | Example row | n/a |
| lineage coverage | upstream/downstream | all models | n/a | Is lineage documented? | lineage review | manifest | complete | PASS | PASS | analytics | none | PASS | Example row | n/a |
| incident history | incidents | n/a | n/a | Are incidents tracked? | incident log | n/a | n/a | n/a | n/a | analytics | none | NOT_APPLICABLE | No incident system linked | When incident system linked |
| mean time to detect | MTTD | n/a | n/a | How fast are issues detected? | incident metrics | n/a | n/a | n/a | n/a | analytics | none | NOT_APPLICABLE | No incident system linked | When incident system linked |
| mean time to resolve | MTTR | n/a | n/a | How fast are issues resolved? | incident metrics | n/a | n/a | n/a | n/a | analytics | none | NOT_APPLICABLE | No incident system linked | When incident system linked |
