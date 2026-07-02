# Semantic Layer Spec

Before creating or changing semantic layer files, follow [phase-plan-approval.md](phase-plan-approval.md), [kpi-definitions.md](kpi-definitions.md), [metric-verification.md](metric-verification.md), [kpi-reconciliation.md](kpi-reconciliation.md), and [cardinality-validation.md](cardinality-validation.md).

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
| Completion criteria | Every semantic metric traces to a documented and reconciled key performance indicator, parse succeeds, semantic metric results match gold SQL checks, and metric grain/cardinality is proven |
| Report required | `reports/agent/semantic_report.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md` |

## Folder

- `models/semantic/{project_slug}/` or co-locate YAML next to mart models
- File: `_{project_slug}_semantic.yml`

## Semantic model design

Create semantic models only from final marts/facts that already build successfully. Use actual final model names, measures, dimensions, and time fields.

Minimum expectations:

- Primary entity matches the fact grain
- Time dimension is explicit when metrics need time analysis
- Measures have clear aggregation and business meaning
- Ratio metrics use safe denominators
- Metric names are business-friendly and documented

Every semantic metric must trace to a key performance indicator definition. Include the key performance indicator's business meaning, grain, numerator, denominator, filters, time field, source model, caveats, approval status, cardinality proof, and metric verification status in the semantic phase report.

If the key performance indicator is not approved, has ambiguous numerator, denominator, filters, or time field, or fails expected-versus-actual reconciliation, do not implement it as a semantic metric. Mark it deferred or blocked and ask for the missing business definition or fix the upstream logic.

## Generic semantic model examples only

| Semantic model | dbt model | Grain entity |
|---|---|---|
| `<business_events>` | `fct_<business_events>` | `<business_event_id>` |
| `<child_business_events>` | `fct_<child_business_events>` | `<child_business_event_id>` |

## Generic metric examples only

| Metric | Type | Definition |
|---|---|---|
| `<event_count>` | simple | count of validated business events |
| `<gross_amount>` | simple | sum of an approved gross amount field |
| `<net_amount>` | simple | sum of an approved net amount field |
| `<quantity_total>` | simple | sum of an approved quantity field |
| `<average_value>` | ratio | approved numerator / approved denominator |

## Example (legacy spec excerpt)

```yaml
version: 2

semantic_models:
  - name: business_events
    model: ref('fct_business_events')
    description: Business-event semantic model for approved metrics
    defaults:
      agg_time_dimension: event_date
    entities:
      - name: business_event
        type: primary
        expr: business_event_id
      - name: business_entity
        type: foreign
        expr: business_entity_id
    dimensions:
      - name: event_date
        type: time
        type_params:
          time_granularity: day
      - name: event_status
        type: categorical
    measures:
      - name: event_count
        agg: count
        expr: business_event_id
      - name: approved_gross_amount
        agg: sum
        expr: case when is_reportable_event then gross_amount else 0 end
      - name: approved_net_amount
        agg: sum
        expr: case when is_reportable_event then net_amount else 0 end

metrics:
  - name: event_count
    label: Event Count
    type: simple
    type_params:
      measure: event_count
  - name: approved_gross_amount
    label: Approved Gross Amount
    type: simple
    type_params:
      measure: approved_gross_amount
  - name: average_event_value
    label: Average Event Value
    type: ratio
    type_params:
      numerator: approved_gross_amount
      denominator: event_count
```

Use **actual column names** from final fact models. Do not invent fields.

## Validate

```powershell
dbt parse --no-partial-parse
```

Also run metric verification SQL from [metric-verification.md](metric-verification.md) and source-to-gold reconciliation from [kpi-reconciliation.md](kpi-reconciliation.md) for each semantic metric. Record expected versus actual results in `reports/agent/semantic_report.md`. If a semantic metric differs from gold SQL, mark semantic delivery `BLOCKED`.

## Do not

- Build semantic models before marts exist
- Use `source()` in semantic YAML - only `ref()` to marts facts/dims
- Create semantic metrics from unreconciled gold columns or dashboard-only assumptions
