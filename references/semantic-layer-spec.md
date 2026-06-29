# Semantic Layer Spec

Before creating or changing semantic layer files, follow [phase-plan-approval.md](phase-plan-approval.md), [kpi-definitions.md](kpi-definitions.md), and [metric-verification.md](metric-verification.md).

**When:** after marts layer builds successfully.
**Skill:** compose with `building-dbt-semantic-layer`.
**dbt Core 1.10.x:** use **legacy spec** (top-level `semantic_models:` and `metrics:`).

## Phase contract

| Area | Contract |
|---|---|
| Inputs required | Approved semantic phase plan, validated marts, approved or clearly supported key performance indicator definitions, metric verification results, time fields, entities, and dimensions |
| Allowed changes | Semantic model YAML, metric YAML, semantic documentation, and semantic phase report |
| Not allowed | New marts, dashboards, guessed metrics, metrics from empty facts, or unapproved sensitive dimensions |
| Commands to run | `dbt parse --no-partial-parse` and any available semantic validation command supported by the installed dbt version |
| Completion criteria | Every semantic metric traces to a documented and reconciled key performance indicator, parse succeeds, and semantic metric results match gold SQL checks |
| Report required | `reports/agent/semantic_report.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md` |

## Folder

- `models/semantic/{domain}/` or co-locate YAML next to mart models
- File: `_{domain}_semantic.yml`

## Semantic model design

Create semantic models only from final marts/facts that already build successfully. Use actual final model names, measures, dimensions, and time fields.

Minimum expectations:

- Primary entity matches the fact grain
- Time dimension is explicit when metrics need time analysis
- Measures have clear aggregation and business meaning
- Ratio metrics use safe denominators
- Metric names are business-friendly and documented

Every semantic metric must trace to a key performance indicator definition. Include the key performance indicator's business meaning, grain, numerator, denominator, filters, time field, source model, caveats, approval status, and metric verification status in the semantic phase report.

If the key performance indicator is not approved, has ambiguous numerator, denominator, filters, or time field, or fails expected-versus-actual reconciliation, do not implement it as a semantic metric. Mark it deferred or blocked and ask for the missing business definition or fix the upstream logic.

## Example semantic models only

| Semantic model | dbt model | Grain entity |
|---|---|---|
| `orders` | `fct_orders` | `order_id` |
| `order_items` | `fct_order_items` | `order_item_id` |

## Example metrics only

| Metric | Type | Definition |
|---|---|---|
| `order_count` | simple | count of orders |
| `gross_revenue` | simple | sum of `gross_amount` on commercial orders |
| `net_revenue` | simple | sum of `net_order_amount` on commercial orders |
| `items_sold` | simple | sum of `quantity` on order items |
| `average_order_value` | ratio | `gross_revenue` / `order_count` |

## Example (legacy spec excerpt)

```yaml
version: 2

semantic_models:
  - name: orders
    model: ref('fct_orders')
    description: Order-level semantic model for revenue metrics
    defaults:
      agg_time_dimension: order_date
    entities:
      - name: order
        type: primary
        expr: order_id
      - name: customer
        type: foreign
        expr: customer_id
    dimensions:
      - name: order_date
        type: time
        type_params:
          time_granularity: day
      - name: order_status
        type: categorical
    measures:
      - name: order_count
        agg: count
        expr: order_id
      - name: gross_revenue
        agg: sum
        expr: case when is_commercial_order then gross_amount else 0 end
      - name: net_revenue
        agg: sum
        expr: case when is_commercial_order then net_order_amount else 0 end

metrics:
  - name: order_count
    label: Order Count
    type: simple
    type_params:
      measure: order_count
  - name: gross_revenue
    label: Gross Revenue
    type: simple
    type_params:
      measure: gross_revenue
  - name: average_order_value
    label: Average Order Value
    type: ratio
    type_params:
      numerator: gross_revenue
      denominator: order_count
```

Use **actual column names** from final fact models. Do not invent fields.

## Validate

```powershell
dbt parse --no-partial-parse
```

Also run metric verification SQL from [metric-verification.md](metric-verification.md) for each semantic metric and record expected versus actual results in `reports/agent/semantic_report.md`.

## Do not

- Build semantic models before marts exist
- Use `source()` in semantic YAML - only `ref()` to marts facts/dims
- Create semantic metrics from unreconciled gold columns or dashboard-only assumptions
