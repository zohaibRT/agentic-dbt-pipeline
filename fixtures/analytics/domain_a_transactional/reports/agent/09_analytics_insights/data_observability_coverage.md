# Data Observability Coverage (TEST FIXTURE)

| Domain | Scope | Models | Metric IDs | Business or Engineering Question | Validation Method | Proof or Telemetry | Threshold or SLA | Expected Result | Actual Result | Owner | Incident or Action | Status | Notes | Reassessment Condition |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| completeness | all gold models | fct_events | orphan_rate | Is completeness healthy? | dbt tests | sql proof | SLA n/a | 0 | 0 | analytics | none | PASS | Checked in fixture | n/a |
| consistency | fixture scope | n/a | n/a | Is consistency monitored? | n/a | n/a | n/a | n/a | n/a | analytics | none | NOT_APPLICABLE | Fixture has no second source or incident system | Reassess when source exists |
| distribution stability | all gold models | fct_events | orphan_rate | Is distribution stability healthy? | dbt tests | sql proof | SLA n/a | 0 | 0 | analytics | none | PASS | Checked in fixture | n/a |
| documentation coverage | all gold models | fct_events | orphan_rate | Is documentation coverage healthy? | dbt tests | sql proof | SLA n/a | 0 | 0 | analytics | none | PASS | Checked in fixture | n/a |
| freshness | fixture scope | n/a | n/a | Is freshness monitored? | n/a | n/a | n/a | n/a | n/a | analytics | none | NOT_APPLICABLE | Fixture has no second source or incident system | Reassess when source exists |
| incident history | fixture scope | n/a | n/a | Is incident history monitored? | n/a | n/a | n/a | n/a | n/a | analytics | none | NOT_APPLICABLE | Fixture has no second source or incident system | Reassess when source exists |
| lineage coverage | all gold models | fct_events | orphan_rate | Is lineage coverage healthy? | dbt tests | sql proof | SLA n/a | 0 | 0 | analytics | none | PASS | Checked in fixture | n/a |
| mean time to detect | fixture scope | n/a | n/a | Is mean time to detect monitored? | n/a | n/a | n/a | n/a | n/a | analytics | none | NOT_APPLICABLE | Fixture has no second source or incident system | Reassess when source exists |
| mean time to resolve | fixture scope | n/a | n/a | Is mean time to resolve monitored? | n/a | n/a | n/a | n/a | n/a | analytics | none | NOT_APPLICABLE | Fixture has no second source or incident system | Reassess when source exists |
| model ownership coverage | all gold models | fct_events | orphan_rate | Is model ownership coverage healthy? | dbt tests | sql proof | SLA n/a | 0 | 0 | analytics | none | PASS | Checked in fixture | n/a |
| pipeline reliability | all gold models | fct_events | orphan_rate | Is pipeline reliability healthy? | dbt tests | sql proof | SLA n/a | 0 | 0 | analytics | none | PASS | Checked in fixture | n/a |
| reconciliation accuracy | all gold models | fct_events | orphan_rate | Is reconciliation accuracy healthy? | dbt tests | sql proof | SLA n/a | 0 | 0 | analytics | none | PASS | Checked in fixture | n/a |
| referential integrity | all gold models | fct_events | orphan_rate | Is referential integrity healthy? | dbt tests | sql proof | SLA n/a | 0 | 0 | analytics | none | PASS | Checked in fixture | n/a |
| row-count stability | all gold models | fct_events | orphan_rate | Is row-count stability healthy? | dbt tests | sql proof | SLA n/a | 0 | 0 | analytics | none | PASS | Checked in fixture | n/a |
| test reliability | all gold models | fct_events | orphan_rate | Is test reliability healthy? | dbt tests | sql proof | SLA n/a | 0 | 0 | analytics | none | PASS | Checked in fixture | n/a |
| timeliness | all gold models | fct_events | orphan_rate | Is timeliness healthy? | dbt tests | sql proof | SLA n/a | 0 | 0 | analytics | none | PASS | Checked in fixture | n/a |
| uniqueness | all gold models | fct_events | orphan_rate | Is uniqueness healthy? | dbt tests | sql proof | SLA n/a | 0 | 0 | analytics | none | PASS | Checked in fixture | n/a |
| validity | all gold models | fct_events | orphan_rate | Is validity healthy? | dbt tests | sql proof | SLA n/a | 0 | 0 | analytics | none | PASS | Checked in fixture | n/a |
