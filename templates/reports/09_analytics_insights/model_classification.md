# Model Classification

Classify every in-scope resource using dbt manifest `unique_id` as the canonical key when a manifest exists. Classes are structural — no fixed business entity or naming prefix is mandatory.

Human approval is required for materially ambiguous classifications. Machine recommendations are advisory only.

| Unique ID | Model | Package | Version | Class | Business Meaning | Business Process | Grain | Key | Date Roles | Measures | Dimensions | Tests | Reconciliation | Materialization | Confidence | Machine Recommendation | Human Approval Status | Exclusion Reason | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| model.package.name | <name> | <package> | <version or blank> | <structural_class> | <meaning> | <process> | <grain> | <key> | <roles> | <fields> | <dims> | <tests> | <status> | <mat> | HIGH/MEDIUM/LOW | <recommended_class> | APPROVED/PENDING_REVIEW/... | <reason if EXCLUDED> | PASS/WARN/BLOCKED/DEFERRED |

Supported structural classes (not all required in every project): source, staging, intermediate, conformed_entity, core_entity, dimension, role_playing_dimension, bridge, transaction_fact, event_fact, factless_fact, periodic_snapshot_fact, accumulating_snapshot_fact, reporting_fact, reporting_mart, reference, catalog, semantic_model, metric, exposure, snapshot, seed, analysis, test, audit, utility, excluded, unsupported, deferred.

Legacy name-only rows are accepted only when the name is unambiguous; migrate to `unique_id`.
