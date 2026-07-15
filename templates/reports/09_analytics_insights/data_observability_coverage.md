# Data Observability Coverage

Domain-neutral observability checklist. Every required domain needs an explicit **Status**.
Use **NOT_APPLICABLE** only with a Notes/reason. **SUPPORTED** counts as PASS.

| Domain | Evidence | Owner | Status | Notes |
|---|---|---|---|---|
| completeness | null-rate tests on grain keys | analytics | PASS | Example row |
| uniqueness | grain uniqueness tests | analytics | PASS | Example row |
| validity | accepted-value tests | analytics | PASS | Example row |
| consistency | cross-check notes | analytics | NOT_APPLICABLE | No second source in scope |
| referential integrity | relationship/orphan proofs | analytics | PASS | Example row |
| reconciliation accuracy | source-to-mart variance proofs | analytics | PASS | Example row |
| freshness | source freshness or SLA note | analytics | NOT_APPLICABLE | Warehouse not connected in dev |
| timeliness | pipeline duration notes | analytics | PASS | Example row |
| row-count stability | volume drift monitoring | analytics | PASS | Example row |
| distribution stability | status mix drift notes | analytics | PASS | Example row |
| pipeline reliability | build success / failed models | analytics | PASS | Example row |
| test reliability | failed test count | analytics | PASS | Example row |
| documentation coverage | model/column docs | analytics | PASS | Example row |
| model ownership coverage | owners in contracts/exposures | analytics | PASS | Example row |
| lineage coverage | documented upstream/downstream | analytics | PASS | Example row |
| incident history | incident log when available | analytics | NOT_APPLICABLE | No incident system linked |
| mean time to detect | MTTD when available | analytics | NOT_APPLICABLE | No incident system linked |
| mean time to resolve | MTTR when available | analytics | NOT_APPLICABLE | No incident system linked |
