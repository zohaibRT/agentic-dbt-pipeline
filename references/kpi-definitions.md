# Key Performance Indicator Definitions

Use this before gold/marts, semantic layer, presentation layer, and final delivery.

## Core rule

Key performance indicators are business definitions, not just SQL expressions. The agent must propose supported key performance indicators from the final marts evidence, but must not silently invent business meaning.

When a key performance indicator can be defined more than one reasonable way, recommend the safest option with evidence and ask for approval before building semantic metrics, reporting marts, dashboards, or presentation artifacts.

## Required definition fields

Every proposed or implemented key performance indicator must include:

| Field | Requirement |
|---|---|
| Name | Simple user-facing name |
| Business meaning | What the metric is intended to answer |
| Source model | Final gold/mart model or approved semantic model |
| Grain | The row grain where the metric is calculated |
| Numerator | Count, sum, or expression being measured |
| Denominator | Required for rates, ratios, averages, and percentages |
| Filters | Included/excluded statuses, types, dates, or entities |
| Time field | Date or timestamp used for trend analysis |
| Dimensions | Safe breakdown fields, such as department, region, category, provider, or customer segment |
| Caveats | Empty upstream data, approximations, privacy limits, or missing definitions |
| Approval status | Agent-recommended, user-approved, deferred, or blocked |

## Advanced metric checks

For rates, ratios, percentages, and averages:

- Define numerator and denominator explicitly.
- Use safe division with a null or zero-denominator guard.
- State whether cancelled, pending, denied, inactive, test, deleted, or draft records are included.
- State the time field that controls the metric.
- Validate the metric with aggregate SQL after the gold/marts build.

For financial or operational metrics:

- State whether amounts are gross, net, billed, paid, collected, estimated, or outstanding.
- State the currency or unit when available.
- Do not use proxy fields as final business metrics without naming the caveat.

For healthcare, finance, people, or other sensitive domains:

- Avoid direct identifier dimensions unless approved.
- Prefer aggregate key performance indicators over record-level personal reporting.

## Required report section

Gold, semantic, presentation, and final reports must include:

```markdown
## Key Performance Indicator Definitions

| Key Performance Indicator | Business Meaning | Source Model | Grain | Numerator | Denominator | Filters | Time Field | Result / Caveat | Approval |
|---|---|---|---|---|---|---|---|---|---|
| <name> | <meaning> | <model> | <grain> | <numerator> | <denominator or not applicable> | <filters> | <date field> | <validation/caveat> | <approved/deferred/blocked> |
```

If no key performance indicators are ready, write `No key performance indicators were implemented because <reason>` and list the missing definitions or data evidence.

## Stop conditions

Stop before semantic layer, presentation layer, or final metric handoff when:

- A key performance indicator depends on a missing or empty fact table.
- The numerator or denominator is ambiguous.
- The time field is ambiguous and changes the metric meaning.
- The metric would expose sensitive or direct identifier data without approval.
- The metric validation result contradicts the definition.
