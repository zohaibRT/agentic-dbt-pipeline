# Power BI Key Performance Indicator And DAX Tooling

Use this when the approved presentation layer is Power BI PBIP/TMDL and the agent needs to generate or validate measures, relationships, or report visuals.

## Core Rule

Power BI implements and validates reporting logic. It does not own the business truth.

Measure generation must be driven by:

1. `reports/agent/kpi_catalog.md`
2. Validated dbt semantic metrics
3. Explicit user-approved requirements

Do not invent Power BI-only key performance indicators, denominators, filters, business flags, or relationship shortcuts just to make a report look complete.

## Ownership Boundaries

| Layer | Owns |
|---|---|
| dbt | Trusted facts, dimensions, surrogate keys, grains, reportable flags, tested relationships, and source-to-gold lineage |
| Analytics insight reporting | Key performance indicator definitions, reporting questions, dashboard pages, visual intent, caveats, and readiness |
| Power BI tooling | DAX measures, semantic model metadata, display folders, relationships, report pages, visuals, and artifact validation |
| PBIP validator | Static file checks, known Power BI Desktop failure guards, relationship audits, and delivery gate evidence |

If a key, relationship path, status flag, amount classification, privacy transformation, or denominator belongs in dbt, build and test it in dbt before exposing it to Power BI.

## Measure Generation Contract

For every generated DAX measure, record the source mapping in `reports/agent/dax_measures.md` and `reports/agent/presentation_report.md`:

| Field | Required |
|---|---|
| Measure label | Simple user-facing name |
| Source key performance indicator | Name from `kpi_catalog.md` or semantic metric |
| Source dbt model | Gold/mart model or semantic model |
| Formula | Approved numerator, denominator, filters, and safe division logic |
| Time field | Approved date or timestamp for trend/time intelligence |
| Grain | Source grain and report grain |
| Allowed dimensions | Safe fields for slicers, drilldowns, and breakdowns |
| Confidence | High, approved, warning, low, blocked, or deferred |
| Caveats | Data quality, empty facts, privacy, mapping, or definition limitations |
| Verification | SQL or semantic query result that reconciles to the DAX result |

Only create measures whose confidence is `HIGH` or user-approved `MEDIUM`. For `LOW`, `BLOCKED`, or `Deferred` key performance indicators, document them as blocked or deferred unless the user explicitly approves further discovery and the metric is rescored.

## Optional Tooling Priority

Use available tooling in this order, without making optional tools a hard dependency:

1. Power BI Modeling Model Context Protocol tools when exposed or installable.
2. `pbi-cli` when already installed or approved for use.
3. Bundled PBIP generator and validator scripts.
4. Static DAX/specification files only when the user approved a non-PBIP handoff or tooling is unavailable and the phase is marked blocked/deferred for full validation.

When Power BI Modeling Model Context Protocol tools are available, use them for model load, table inspection, relationship inspection, DAX validation or smoke queries, and report the results. Availability without use is a validation failure for PBIP/TMDL delivery.

When `pbi-cli` is available, use it as an optional helper for DAX validation, semantic model audits, relationship checks, and report-layer inspection. Do not require `pbi-cli` for the skill to work, and do not let it bypass dbt or analytics insight definitions.

Use `pbi-tools` only for source-control or DevOps-oriented Power BI workflows when explicitly useful. Do not treat it as the primary key performance indicator definition or DAX authoring tool.

## Anti-Patterns

Do not:

- Create missing surrogate keys, composite keys, business flags, or denominator logic inside Power BI M or DAX when they should be modeled in dbt.
- Add Power Query M steps such as `AddedKey = Table.AddColumn(...)` as a shortcut for missing dbt model logic.
- Create a DAX measure when the numerator, denominator, filter, grain, or time field is not documented.
- Create direct active relationships that bypass the approved star schema or introduce ambiguous filter paths.
- Use Power BI measures to hide an upstream dbt logic bug.
- Mark presentation complete when DAX results do not reconcile to gold or semantic SQL.

## Required Validation

Before marking a Power BI phase complete:

1. Confirm every DAX measure maps to `kpi_catalog.md`, a validated semantic metric, or approved user requirement.
2. Recalculate every key performance indicator with SQL against gold/marts or with an approved semantic query.
3. Compare expected versus actual numerator, denominator, and final result for rates, ratios, averages, and percentages.
4. Validate relationship paths for ambiguity.
5. Run `scripts/validate_powerbi_pbip.py` for PBIP/TMDL artifacts when available.
6. Run Power BI Modeling Model Context Protocol validation when available.
7. Run Power BI Desktop open validation when available.
8. Record tool availability, commands, results, failures, and unresolved validation gaps in `reports/agent/presentation_report.md`.

If validation cannot run, do not claim the PBIP opens or the semantic model loads. Mark the unavailable check as `NOT RUN` with the reason, or mark the phase `BLOCKED` when the missing check is required for delivery.
