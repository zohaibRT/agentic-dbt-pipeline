# Advanced Data Engineering Review

Use this before final delivery and whenever a full pipeline claims to be complete.

## Core rule

The agent must do a senior data-engineering review, not only a dbt command check. This is a required final gate.

## Review areas

| Area | What to verify |
|---|---|
| Source control | Approved source lock was followed; no silent database, schema, or domain switch |
| Schema hygiene | Source schema stayed read-only; profile target schema hygiene passed; packages routed outside source |
| Layer correctness | Bronze, silver, and gold each built and passed data validation queries |
| Grain and joins | Every model has one clear grain; joins did not create unplanned row multiplication |
| Bridge tables | Many-to-many relationships were reviewed; required bridges were built and tested, or deferrals were documented with evidence |
| Tests | Key uniqueness, not-null, relationship, accepted values, mapping coverage, and important business-rule tests exist where relevant |
| Data quality | Empty tables, row-count movement, date coverage, status distributions, and measure sanity are documented |
| Privacy | Sensitive fields, direct identifiers, personally identifiable information, and protected health information are excluded, masked, hashed, or approved |
| Key performance indicators | Metrics have business meaning, source model, grain, numerator, denominator, filters, time field, caveats, validation evidence, and approval status |
| Semantic layer | Semantic metrics trace to supported final marts and approved or clearly supported key performance indicators with `KPI_DEFINITION_CONTRACTS.md` and `METRIC_VERIFICATION_MATRIX.md` evidence |
| Project evaluator | Warnings are fixed, documented, or explicitly accepted; no architecture-breaking fixes were used |
| Documentation | `dbt docs generate` ran; docs include model purpose, grain, assumptions, and important columns |
| Analytics insight reporting | Trusted reporting design files exist under `reports/agent/`; trusted vs deferred outputs are separated; presentation scope is documented before artifact build |
| Presentation layer | A presentation-layer recommendation was produced after analytics insight reporting, or the report explains why it is blocked or skipped |
| Operations | Commit status, continuous integration status, Agents Schema status, and run commands are documented |
| Principal standards | State-based continuous integration readiness, contracts/versioning, package and macro usage, Power BI storage mode, bridge tables, aggregate tables, modern table formats, warehouse optimization, and SQL style are applied, deferred, or marked not applicable |

## Required report section

Add this section to the final report and final handoff:

```markdown
## Advanced Data Engineering Review

| Area | Status | Evidence | Action Needed |
|---|---|---|---|
| <area> | <PASS/WARN/FAIL/BLOCKED/SKIPPED> | <evidence> | <next action or none> |
```

Do not mark the pipeline complete when the review has an unresolved `FAIL` or `BLOCKED` item.

`WARN` is acceptable only when the caveat is explained and the data engineer can review it later without risking silent incorrect outputs.
