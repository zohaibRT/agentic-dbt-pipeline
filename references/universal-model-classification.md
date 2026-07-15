# Universal Model Classification

Use during discovery, layer builds, analytics insight reporting, and acceptance.

Also read [analytics-product-completeness.md](analytics-product-completeness.md) and [evidence-driven-dbt-process.md](evidence-driven-dbt-process.md).

## Core rule

Classify **every included resource** from current-project evidence using dbt manifest `unique_id` as the canonical identity when a manifest exists. Do not require fixed business entity names. A structural class is required only when evidence supports it. Naming prefixes (`fct_`, `dim_`, `mart_`) are fallback hints only.

Illustrative only — do not treat as required model names or metric logic: `dim_customer`, `fct_orders`, `fct_payments`.

See also [docs/manifest-resource-identity-migration.md](../docs/manifest-resource-identity-migration.md).

## Allowed model classes

| Class | Meaning |
|---|---|
| source | Upstream warehouse table declared as a dbt source |
| staging | Source-shaped cleaning / renaming layer (`stg_*` or equivalent) |
| intermediate | Business-process or entity prep (`int_*` or equivalent) |
| conformed/core entity | Shared entity definitions (may live in intermediate or gold) |
| fact/event | Generic measurable event when subtype is unclear |
| transaction fact | Financial or quantity transactions |
| periodic snapshot fact | Point-in-time balances or statuses |
| accumulating snapshot fact | Lifecycle with multiple milestones |
| dimension | Descriptive entity or attribute table |
| bridge | Validated many-to-many relationship |
| reference/catalog | Low-change lookup / reference |
| reporting mart | Business-facing aggregated or wide table |
| semantic model | MetricFlow / semantic YAML surface |
| exposure | Downstream consumer declaration |
| audit/system | Audit, logs, jobs, oauth, platform internals |
| excluded | Out of scope with documented reason |

`core/` / conformed models are conceptual. They do **not** require a physical `models/core/` folder.

## Required classification fields

Write to:

```text
reports/agent/09_analytics_insights/model_classification.md
```

| Field | Required |
|---|---|
| model name | yes |
| model class | yes |
| business meaning | yes when included |
| source system | when known |
| grain | required for facts/dims/marts |
| primary or natural key | required for facts/dims |
| foreign keys | when present |
| date fields and date roles | when present |
| measurable fields | when present |
| descriptive fields | when present |
| status/type fields | when present |
| sensitive fields | when present |
| supported dimensions | for facts/marts |
| downstream consumers | when known |
| tests | list or none |
| reconciliation status | for material facts/KPIs |
| materialization | yes for built models |
| refresh behavior | when known |
| business owner | when known |
| confidence | yes |
| status | PASS / WARN / BLOCKED / DEFERRED |

## Suggested table

```markdown
# Model Classification

| Model | Class | Business Meaning | Grain | Key | Date Roles | Measures | Dimensions | Tests | Reconciliation | Materialization | Confidence | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| <model> | <class> | <meaning> | <grain> | <key> | <roles> | <fields> | <dims> | <tests> | <status> | <mat> | HIGH/MEDIUM/LOW | PASS/WARN/BLOCKED/DEFERRED |
```

## Acceptance

- 100% of in-scope built models appear in the classification register.
- Unclassified included models are a FAIL for analytics product completeness.
- Excluded models must carry an exclusion reason.
