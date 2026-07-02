# Intermediate Layer Spec

## Goal

Create or update **only** the intermediate layer from completed staging models.

If `project_rules` include manual mappings or code translations, read [mapping-seeds.md](mapping-seeds.md) before modeling.
Read [layer-data-validation.md](layer-data-validation.md) and [cardinality-validation.md](cardinality-validation.md) before marking intermediate complete.
Before creating or changing intermediate files, follow [phase-plan-approval.md](phase-plan-approval.md).

## Phase contract

| Area | Contract |
|---|---|
| Inputs required | Approved intermediate phase plan, validated staging models, relationship/cardinality evidence, mapping requirements, and business process understanding |
| Allowed changes | Intermediate SQL models, intermediate YAML, intermediate tests, mapping seeds when approved, and intermediate documentation |
| Not allowed | Marts, semantic metrics, dashboards, direct source reads, joins with unproven cardinality, or final reporting calculations |
| Commands to run | `dbt parse --no-partial-parse`, `dbt build --select +path:models/{layer_2_name}/{project_slug}`, and intermediate data validation queries |
| Completion criteria | Reusable business logic has clear grain, joins do not unexpectedly lose or multiply rows, cardinality proof exists, mappings are covered, and validation results are documented |
| Report required | `reports/agent/intermediate_report.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md` |

## Folder and naming

- Folder: `models/{layer_2_name}/{project_slug}/` (default: `models/silver/{project_slug}/`)
- SQL: `int_{source}__<name>.sql`
- YAML: `_int_{source}.yml`

Do not create `models/intermediate/` unless `{layer_2_name}` is explicitly configured as `intermediate`. With default layer names, intermediate models live in `models/silver/{project_slug}/`.

## Model design pattern

Create intermediate models that match the source domain and business process. Do not force ecommerce-shaped models unless the source data is ecommerce.

Use these patterns:

- Aggregate child/event tables to a stable parent grain before joining
- Enrich core business entities with clean attributes and reusable flags
- Join mapping seeds or reference tables after staging
- Keep one clear grain per intermediate model
- Create reusable metrics at the lowest safe grain, but do not create final BI marts here

## Example pattern only

Use this as an example of shape and grain, not as a required model list:

| Model | Grain | Source |
|---|---|---|
| `int_{source}__payments_aggregated` | order_id | `stg_*__payments` |
| `int_{source}__refunds_aggregated` | order_id | `stg_*__refunds` |
| `int_{source}__orders_enriched` | order_id | orders + customers + channels + payment/refund aggregates |
| `int_{source}__order_items_enriched` | order_item_id | order_items + products + categories + orders enriched |
| `int_{source}__customer_order_metrics` | customer_id | all customers + order rollups |

## Business logic (orders enriched example)

Only apply this ecommerce example when the source data actually contains these concepts.

- `order_subtotal_amount` = `gross_amount - discount_amount`
- `calculated_order_total_amount` = subtotal + `tax_amount` + `shipping_amount`
- `net_order_amount` = calculated total - `total_refund_amount`
- `is_cancelled_order` = status = `cancelled`
- `is_refunded_order` = status = `refunded`
- `is_completed_order` = status = `completed`
- `is_commercial_order` = status in (`completed`, `refunded`)

## Payments aggregated example

- `successful_payment_amount` where `payment_status = 'paid'`
- `refunded_payment_amount` where `payment_status = 'refunded'`
- Include totals, counts, first/last dates, method summary if safe

## Customer metrics example

- Include **all customers** (left join), even with no orders
- `is_repeat_customer` = `commercial_orders >= 2`
- Do not allocate refunds to item grain

## Rules

- `ref()` only - **no** `source()` in intermediate
- `{{ config(materialized='view') }}` on every model
- Use **actual** staging/intermediate columns - do not assume `currency_code`, `source_system`, `order_total_amount`, `item_total_amount`
- If a required column is missing, **stop and explain**
- Do not join tables with different grains until duplicates and cardinality are understood
- If a join can multiply rows, aggregate first or ask the user for the correct grain
- Record join safety, row multiplier, row loss, and first unexpected cardinality change in `reports/agent/join_safety_report.md`

## Tests

- `not_null` + `unique` on primary keys
- `relationships` to staging or related intermediate models where safe
- `accepted_values` on boolean flags (`true`, `false`)
- Use modern generic test `arguments:` nesting when supported by the installed dbt version
- Add mapping coverage tests when mapping seeds or code translations are used

## Validate (required after every intermediate change)

Run from dbt project root. **Build is mandatory** - a layer is not complete until build passes.

```powershell
dbt parse --no-partial-parse
dbt build --select +path:models/{layer_2_name}/{project_slug}
```

`+path` builds intermediate models, their tests, and required upstream (staging) dependencies.

After the build, run [layer-data-validation.md](layer-data-validation.md). For intermediate models, the report must show row counts, expected-empty evidence, grain duplicate checks, join relationship checks, row-loss or row-multiplication checks against staging/upstream models, derived flag/value distributions, mapping coverage when mappings are used, and important measure sanity checks. Share the intermediate validation results with the user before asking for commit or moving to marts.

## Do not create

marts, facts, dimensions, semantic models, metrics, reports
