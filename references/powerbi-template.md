# Power BI Template System

Use this only when the user explicitly approves generated Power BI PBIP/TMDL mode, or when validating the bundled neutral PBIP template. For the normal presentation-layer approval path, use [powerbi-thin-model-template.md](powerbi-thin-model-template.md) first.

Read [powerbi-official-docs.md](powerbi-official-docs.md) with this file. The official Microsoft Learn pages are the source of truth when PBIP/PBIR/TMDL project layout or preview behavior is uncertain.

## Purpose

The skill bundles a neutral PBIP/PBIR/TMDL template so generated reports do not depend on random local projects on one developer machine.

Default template:

```text
assets/powerbi/pbip_template/
```

Public generator:

```text
scripts/generate_powerbi_pbip.py
```

Low-level template copier:

```text
scripts/create_powerbi_pbip_from_template.py
```

Static validator:

```text
scripts/validate_powerbi_pbip.py
```

## Template Rules

The bundled template must stay neutral. It must not include:

- Customer-specific table names.
- Customer-specific key performance indicators.
- IHMS, ShopSphere, hospital, travel, Odoo, or other domain-specific logic.
- Source credentials or connection strings.
- Old DAX business logic.
- Reused relationships.
- Reused lineage tags or `.platform` logical IDs.
- Business-specific report page names.
- Customer branding unless it is generic and optional.
- Invalid linguistic metadata or JSON payloads inside XML-typed metadata content.
- SemanticModel `definition/cultures/` files or `ref cultureInfo` references unless exact target-version Desktop-generated support was approved and validated.

The template should only provide:

- Valid `.pbip` structure.
- Valid `.Report/` folder structure.
- Valid `.SemanticModel/` folder structure.
- Valid PBIR metadata pattern.
- Valid TMDL semantic model metadata pattern.
- Placeholder names and IDs.
- Empty or minimal generic report shell.
- Required `.platform` files.
- Known-good report metadata and version pattern.

## Generation Flow

0. Generated PBIP mode is not the default presentation technology. If the user approves a presentation layer without naming a technology, use [matplotlib-presentation-layer.md](matplotlib-presentation-layer.md). If the user explicitly chooses Power BI without asking the agent to generate the full PBIP, use [powerbi-thin-model-template.md](powerbi-thin-model-template.md): create the handoff folder/checklist, ask the human to connect data in Power BI Desktop, save the PBIP at the requested path, and wait for confirmation.
1. Use `scripts/generate_powerbi_pbip.py` only after the user explicitly approves generated PBIP mode or when validating the bundled template itself.
2. Generate into the project, usually under `reports/powerbi/<project_name>/`.
3. Read [powerbi-kpi-dax-tooling.md](powerbi-kpi-dax-tooling.md), then read and use these planning inputs when available:
   - `reports/agent/09_analytics_insights/dashboard_spec.md`
   - `reports/agent/09_analytics_insights/kpis/kpi_catalog.md`
   - `reports/agent/KPI_DEFINITION_CONTRACTS.md`
   - `reports/agent/METRIC_VERIFICATION_MATRIX.md`
   - `reports/agent/09_analytics_insights/reporting_catalog.md`
   - `reports/agent/09_analytics_insights/analytics_insight_report.md`
   - `reports/agent/09_analytics_insights/reporting_readiness_scorecard.md`
   - `reports/agent/09_analytics_insights/insight_backlog.md`
   - `target/manifest.json`
   - `target/catalog.json`
   - `target/semantic_manifest.json`
4. Add project-specific tables, relationships, measures, parameters, source partitions, pages, slicers, key performance indicator cards, and visuals only from validated dbt gold models, semantic metrics, analytics insight outputs, and explicit user-approved requirements.
5. Regenerate all project-specific IDs and lineage tags. Do not reuse fixed template IDs.
6. Never write credentials into PBIP, TMDL, PBIR, JSON, or Markdown handoff files.
7. Do not generate linguistic metadata or SemanticModel culture files by default. XML content type requires XML; JSON content type requires JSON. Omit linguistic/culture schema artifacts unless exact target-version Desktop-generated support was approved and validated.
8. Detect Power BI Desktop with `python scripts/detect_powerbi_desktop.py` when Desktop validation is expected.
9. Run `python scripts/validate_powerbi_pbip.py <generated_pbip_folder>`, and run version-aware validation with `--require-powerbi-desktop-version --powerbi-desktop-version <version>` when the Desktop version is available.
10. Continue with Power BI Modeling Model Context Protocol validation and Power BI Desktop open validation when available.
11. Write or update the presentation reports required by [presentation-layer.md](presentation-layer.md).

## Fallback Priority

Use this priority order:

1. Use the human-connected Power BI Desktop template workflow when the user explicitly chooses Power BI. The agent creates the handoff folder and exact PBIP path, then waits while the human connects data and saves the PBIP.
2. Use a user-approved existing Power BI Desktop-created PBIP template through the thin model workflow.
3. Use the bundled neutral PBIP template from `assets/powerbi/pbip_template/` only when generated PBIP mode is explicitly approved.
4. If generated PBIP mode is approved and the bundled template is missing, use `scripts/generate_powerbi_pbip.py` or the current generator logic to create a minimal PBIP/PBIR/TMDL skeleton, then validate it.
4. Use an existing local PBIP only as a reference when:
   - The exact path is shown to the user.
   - The user explicitly approves it.
   - The agent sanitizes before use.
   - Business-specific content, credentials, relationships, measures, page names, visuals, source connections, `.pbi/` cache files, lineage tags, and logical IDs are not copied unless explicitly approved.

Never silently adapt a nearby local PBIP project.

## Validation Language

Keep these validation results separate:

- PBIP structural validation: file tree, `.pbip`, Report artifact, SemanticModel artifact, JSON parsing, `.platform`, PBIR/PBIP links.
- TMDL/PBIR validation: TMDL syntax risks, lineage tags, keys, relationships, partitions, measures table, report pages and visuals.
- Power BI Modeling Model Context Protocol validation: `ConnectFolder` or equivalent, model/table/relationship inspection, DAX smoke query.
- Power BI Desktop open validation: actual Desktop open/load result when Desktop is available.

Do not claim Power BI Desktop validation passed unless Power BI Desktop or an approved Desktop validation path actually ran.

## Required Checks

Before presentation delivery, verify:

- Bundled template was found or generator fallback was documented.
- If a Desktop-created template was used, the exact template path was approved, copied to the output location, and physical source partitions, M expressions, connection definitions, physical tables, and relationships were not changed unless explicitly approved.
- No credentials are present in generated files.
- No duplicate `lineageTag` values exist.
- No invalid linguistic metadata content-type mismatch exists; JSON such as `{ "Version": "1.0.0" }` must never appear inside XML-typed metadata content.
- No SemanticModel `definition/cultures/` files or `ref cultureInfo` references exist unless exact target-version Desktop-generated support was approved and validated.
- No hardcoded source schema/table assumptions bypass the approved gold schema.
- Power BI one-side relationship keys are unique and not null in dbt.
- Composite business keys use tested surrogate keys.
- Calculated metrics or measures table columns such as `MetricKey` include `sourceColumn` metadata such as `sourceColumn: [MetricKey]`; treat `PFE_TM_METADATA_CALCTABLE_COLUMN_MISSING_SOURCECOLUMN` as a validation failure.
- `scripts/validate_powerbi_pbip.py` passes.
- Power BI Desktop version was detected or recorded as unavailable; version-aware validation passed when the version was available.
- `dashboard_spec.md`, `KPI_DEFINITION_CONTRACTS.md`, `METRIC_VERIFICATION_MATRIX.md`, and `kpi_catalog.md` were used or their absence was documented as blocking/deferred.
- Every generated DAX measure maps to `KPI_DEFINITION_CONTRACTS.md`, `METRIC_VERIFICATION_MATRIX.md`, `kpi_catalog.md`, a validated semantic metric, or an explicit user-approved requirement.
- Optional Power BI Modeling Model Context Protocol tools and `pbi-cli` availability were checked when measure/model validation is needed, and the presentation report records whether they were used, unavailable, skipped with reason, or blocked.
- Blocked or deferred visuals from `insight_backlog.md` were not generated.

Record the results in `reports/agent/10_presentation/presentation_report.md`.
