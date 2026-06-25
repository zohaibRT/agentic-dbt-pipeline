# Marts / Star Schema Layer Spec

## Goal

Create or update **only** the marts star-schema layer from staging + intermediate models.

Read [human-review.md](human-review.md) before marking marts complete if metrics, grain, mappings, or sensitive fields require business approval.
Read [privacy-and-unknown-fields.md](privacy-and-unknown-fields.md) before exposing direct identifiers, sensitive fields, protected health information, personally identifiable information, or unclear coded fields in marts.
Read [layer-data-validation.md](layer-data-validation.md) before marking marts complete.
Read [kpi-definitions.md](kpi-definitions.md) before adding reporting marts or metric-ready fields.
Before creating or changing marts files, follow [phase-plan-approval.md](phase-plan-approval.md).

## Phase contract

| Area | Contract |
|---|---|
| Inputs required | Approved marts phase plan, validated staging/intermediate models, agreed grains, privacy decisions, and key performance indicator definitions or deferrals |
| Allowed changes | Fact models, dimension models, reporting mart models, marts YAML, marts tests, semantic-ready fields, and key performance indicator documentation |
| Not allowed | Semantic layer files, dashboards, reports, unclear metric implementation, direct source reads, or unapproved sensitive-field exposure |
| Commands to run | `dbt parse --no-partial-parse`, `dbt build --select +path:models/{layer_3_name}/{domain}`, and marts data validation queries |
| Completion criteria | Facts and dimensions have documented grains, tests pass, non-empty expectations are verified, metric sanity checks pass, and privacy exposure is reviewed |
| Report required | `reports/agent/marts_report.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md` |

## Folder and naming

- Folder: `models/{layer_3_name}/{domain}/` (default: `models/gold/{domain}/`)
- YAML: `_<domain>_marts.yml`

## Domain-driven design

Build marts from the actual source profile and business requirements. Do not force ecommerce-shaped dimensions or facts unless the source data is ecommerce.

Choose:

- Facts for measurable business events or transactions
- Dimensions for descriptive business entities
- Date dimensions or time spines when date analysis is required
- Reporting marts only when they directly support a known dashboard, KPI, or stakeholder question

Each final model must have a documented grain.

## Key performance indicators

For every reporting mart or metric-ready fact, define supported key performance indicators using [kpi-definitions.md](kpi-definitions.md). The gold phase plan and report must include business meaning, source model, grain, numerator, denominator, filters, time field, dimensions, caveats, validation evidence, and approval status.

If a key performance indicator is plausible but not ready, list it as deferred with the missing definition or data evidence. Do not create final reporting marts only to support ambiguous metrics.

## Example dimensions only

| Model | Grain | Notes |
|---|---|---|
| `dim_customers` | customer_id | staging customers + customer order metrics |
| `dim_products` | product_id | products + categories |
| `dim_categories` | category_id | categories |
| `dim_marketing_channels` | channel_id | channels + fallback row `channel_id = -1`, `channel_name = 'Unattributed'` |
| `dim_dates` | date_day | `generate_series` spine from order/payment/refund/signup dates |

## Example facts only

| Model | Grain | Source |
|---|---|---|
| `fct_orders` | order_id | `int_*__orders_enriched` |
| `fct_order_items` | order_item_id | `int_*__order_items_enriched` |

Map null `channel_id` -> `-1` in facts.

## Optional reporting marts (create if simple)

Create reporting marts only when the required metrics and grain are clear. Do not invent dashboard outputs.

| Model | Grain | Metrics |
|---|---|---|
| `mart_channel_performance` | channel_id | orders by status, gross/net revenue, refund amount, AOV |
| `mart_product_performance` | product_id | items sold, quantity, gross/commercial item revenue, order count |

`average_order_value` = `gross_revenue / commercial_orders` (nullif denominator 0).

## Rules

- `ref()` only - **no** `source()` in marts
- Materialization: follow [materialization-rules.md](materialization-rules.md)
  - `prod`: marts folder `table`; `fct_*` incremental with `unique_key`
  - `dev`: all `view`
- Sync `dbt_project.yml` with `materialization_profile` before build
- Keep facts/dims clean for BI and future semantic layer
- Do not assume unavailable columns (`currency_code`, `source_system`, etc.)
- Do not allocate refunds to order items (refunds are order-grain only)
- Expose business-friendly mapped fields from intermediate models; keep raw codes only when useful for audit
- Do not expose private, sensitive, protected health information, personally identifiable information, or direct identifier fields in marts unless the user explicitly approves
- Default to excluding, masking, or hashing direct identifiers in marts; clear-text exposure is not the default even for local development
- Exclude ambiguous, placeholder, abbreviated, generic, or poorly named fields from marts by default unless definitions are provided or the user approves raw audit exposure
- Keep one clear grain per fact or dimension; do not mix event, entity, and summary grains in the same model
- Add surrogate keys only when natural keys are missing, composite, unstable, or too wide for downstream use

## Tests

- `not_null` + `unique` on dimension and fact primary keys
- `relationships`: facts -> dimensions (and `fct_order_items` -> `fct_orders`)
- `accepted_values` on boolean flags
- Use modern generic test `arguments:` nesting when supported by the installed dbt version
- Add tests for mapping coverage and metric denominators where applicable

## Validate (required after every marts change)

Run from dbt project root. **Build is mandatory** - a layer is not complete until build passes.

```powershell
dbt parse --no-partial-parse
dbt build --select +path:models/{layer_3_name}/{domain}
```

`+path` builds marts models, their tests, and required upstream (staging + intermediate) dependencies.

After the build, run [layer-data-validation.md](layer-data-validation.md). For marts, the report must show row counts for every fact, dimension, and reporting mart; expected-empty evidence for zero-row models; fact and dimension grain checks; fact-to-dimension or fact-to-parent-fact relationship checks; key performance indicator measure sanity checks; date coverage; and privacy exposure checks. Also include the `Key Performance Indicator Definitions` section from [kpi-definitions.md](kpi-definitions.md). If supporting upstream data exists but a gold model is empty, mark the phase `FAIL` or `BLOCKED`, share the evidence with the user, and do not continue to semantic layer, documentation, presentation layer, or final delivery until the issue is fixed or explicitly accepted.

## Do not create

semantic models, metrics, reports, dashboards, final documentation
