# Fact Coverage Contracts (TEST FIXTURE)

| Unique ID | Fact | Grain | Counting Key | Primary Date | Volume | Amount or Quantity | Duration or Balance | Status Distribution | Lifecycle | Dimensions | Time Trends | Period Comparison | Data Quality | Exceptions | Aging | Reconciliation | Business Questions | Notes | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| model.domain_b_encounter.activity_events | activity_events | one row per event | event_id | event_date | SUPPORTED | SUPPORTED | NOT_APPLICABLE | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | NOT_APPLICABLE | SUPPORTED | volume and completion | Fixture | PASS |
| model.domain_b_encounter.fct_encounters | fct_encounters | one row per event | event_id | event_date | SUPPORTED | SUPPORTED | NOT_APPLICABLE | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | NOT_APPLICABLE | SUPPORTED | volume and completion | Fixture | PASS |
