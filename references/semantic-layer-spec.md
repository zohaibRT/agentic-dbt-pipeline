# Semantic Layer Spec

**When:** after marts layer builds successfully.  
**Skill:** compose with `building-dbt-semantic-layer`.  
**dbt Core 1.10.x:** use **legacy spec** (top-level `semantic_models:` and `metrics:`).

## Folder

- `models/semantic/ecommerce/` or co-locate YAML next to mart models
- File: `_ecommerce_semantic.yml`

## Required semantic models (ecommerce reference)

| Semantic model | dbt model | Grain entity |
|---|---|---|
| `orders` | `fct_orders` | `order_id` |
| `order_items` | `fct_order_items` | `order_item_id` |

## Required metrics (minimum)

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

Use **actual column names** from `fct_orders` / `fct_order_items` — do not invent fields.

## Validate

```powershell
& "$env:APPDATA\Python\Python312\Scripts\dbt.exe" parse --no-partial-parse
```

## Do not

- Build semantic models before marts exist
- Use `source()` in semantic YAML — only `ref()` to marts facts/dims
