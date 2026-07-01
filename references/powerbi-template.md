# Power BI Template System

Use this when the approved presentation layer is Power BI PBIP/TMDL.

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

1. Use `scripts/generate_powerbi_pbip.py`.
2. Generate into the project, usually under `reports/powerbi/<project_name>/`.
3. Read and use these planning inputs when available:
   - `reports/agent/dashboard_spec.md`
   - `reports/agent/kpi_catalog.md`
   - `reports/agent/reporting_catalog.md`
   - `reports/agent/analytics_insight_report.md`
   - `reports/agent/reporting_readiness_scorecard.md`
   - `reports/agent/insight_backlog.md`
   - `target/manifest.json`
   - `target/catalog.json`
   - `target/semantic_manifest.json`
4. Add project-specific tables, relationships, measures, parameters, source partitions, pages, slicers, key performance indicator cards, and visuals only from validated dbt gold models, semantic metrics, and analytics insight outputs.
5. Regenerate all project-specific IDs and lineage tags. Do not reuse fixed template IDs.
6. Never write credentials into PBIP, TMDL, PBIR, JSON, or Markdown handoff files.
7. Do not generate linguistic metadata by default. Preserve bundled template metadata only when it validates. XML content type requires XML; JSON content type requires JSON.
8. Run `python scripts/validate_powerbi_pbip.py <generated_pbip_folder>`.
9. Continue with Power BI Modeling Model Context Protocol validation and Power BI Desktop open validation when available.
10. Write or update the presentation reports required by [presentation-layer.md](presentation-layer.md).

## Fallback Priority

Use this priority order:

1. Use the bundled neutral PBIP template from `assets/powerbi/pbip_template/`.
2. If the bundled template is missing, use `scripts/generate_powerbi_pbip.py` or the current generator logic to create a minimal PBIP/PBIR/TMDL skeleton, then validate it.
3. Use an existing local PBIP only as a reference when:
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
- No credentials are present in generated files.
- No duplicate `lineageTag` values exist.
- No invalid linguistic metadata content-type mismatch exists; JSON such as `{ "Version": "1.0.0" }` must never appear inside XML-typed metadata content.
- No hardcoded source schema/table assumptions bypass the approved gold schema.
- Power BI one-side relationship keys are unique and not null in dbt.
- Composite business keys use tested surrogate keys.
- `scripts/validate_powerbi_pbip.py` passes.
- `dashboard_spec.md` and `kpi_catalog.md` were used or their absence was documented as blocking/deferred.
- Blocked or deferred visuals from `insight_backlog.md` were not generated.

Record the results in `reports/agent/presentation_report.md`.
