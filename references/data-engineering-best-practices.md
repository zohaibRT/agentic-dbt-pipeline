# Data Engineering Best Practices

Use this as the final design guardrail for every dbt project.

## Grain and keys

- Define one clear grain for every staging, intermediate, fact, dimension, and mart model.
- Add uniqueness and not-null tests for primary keys when a stable key exists.
- Add relationship tests only when the relationship is confirmed and safe.
- Stop and ask when a join can multiply rows unexpectedly.

## Layer responsibilities

- Sources: represent raw warehouse tables generated from real metadata.
- Staging: rename, cast, standardize, and lightly clean one source table at a time.
- Intermediate: join, map, aggregate, and apply reusable business logic.
- Marts: expose BI-ready facts, dimensions, reporting marts, and semantic metrics.
- Semantic layer: define final business metrics on marts, not on raw or staging tables.

## Incremental and history

- Use incremental facts only when there is a reliable unique key and update/filter column.
- Document the incremental filter and late-arriving-data assumption.
- Add dbt snapshots when slowly changing dimensions or historical attributes matter.
- Do not add snapshots by default; ask when source history, effective dates, or change tracking are unclear.
- Require approval before full-refresh on large or production tables.

## Data quality

- Test primary keys, foreign keys, accepted values, mapping coverage, and important business rules.
- Add source freshness only when a reliable loaded-at timestamp exists.
- Compare row counts and important aggregates between source, staging, intermediate, and marts.
- Use `audit_helper` for refactors, migrations, or old-vs-new validation.

## Contracts and documentation

- Document model purpose, grain, assumptions, limitations, and important columns.
- Use model contracts or enforced column types only when the project and adapter support them safely.
- Add exposures when final marts feed dashboards, reports, notebooks, reverse ETL, or downstream apps.
- Keep metric definitions in one place and avoid duplicate KPI logic across marts.

## Privacy and governance

- Keep direct identifiers, PII, PHI, and sensitive fields out of marts unless explicitly approved.
- Mask, hash, or exclude sensitive fields according to project rules.
- Do not print or commit credentials, private data samples, or full sensitive records.
- Use least-privilege schemas and avoid production changes without approval.

## Performance and operations

- Avoid unnecessary `select *` in marts when tables are wide or sensitive.
- Materialize high-use marts as tables or incremental models in production.
- Keep development builds light with views where possible.
- Run project evaluator after marts and document accepted warnings.
- Keep CI focused on parse, deps, targeted builds, docs, and package checks.
