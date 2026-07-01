# Power BI PBIP Desktop Requirements

Use this when the user approves a Power BI presentation layer, PBIP project, TMDL semantic model, or Power BI Desktop report artifact.

These rules are domain-neutral. Apply them to any gold/mart schema after validating the current project's facts, dimensions, measures, relationships, privacy rules, and reporting scope.

## Bundled neutral template

Use the bundled neutral template at `assets/powerbi/pbip_template/` as the default starting structure for generated PBIP/TMDL projects. Instantiate it with:

```bash
python scripts/generate_powerbi_pbip.py --name <safe_pbip_name> --display-name "<report display name>" --output-dir <powerbi_parent_folder> --project-root <project_root>
```

Then add project-specific tables, source partitions, relationships, measures, pages, visuals, and handoff documentation from validated dbt gold/semantic evidence.

Do not depend on finding a local existing PBIP project on the user's machine. If the agent finds a local PBIP such as IHMS, ShopSphere, Hospital, or another nearby project, it may use that project only as an optional structural reference after showing the exact path and receiving user approval. Never copy source connections, business content, page names, visuals, measures, relationships, branding, `.pbi/` cache files, logical IDs, lineage tags, or source database names from a local reference unless explicitly approved.

Every generated PBIP must regenerate Report and SemanticModel `.platform` logical IDs and TMDL lineage tags, then pass `scripts/validate_powerbi_pbip.py`.

## Enhanced PBIR report layout

For current Power BI Desktop enhanced PBIR projects, create a complete report artifact, not only a semantic model or Markdown plan:

- Root `.pbip` shortcut points to an existing `<name>.Report` artifact folder through the required `report` property.
- `<name>.Report/definition.pbir` exists at the Report artifact root, not under `definition/`.
- `definition.pbir` uses the expected ReportDefinition schema for the target Desktop format and includes `datasetReference.byPath.path` pointing to the `<name>.SemanticModel` artifact.
- `<name>.Report/definition/report.json` exists.
- `<name>.Report/definition/version.json` exists.
- `<name>.Report/definition/pages/pages.json` exists with `pageOrder` and a valid active page when one is declared.
- Do not keep legacy `<name>.Report/report.json` at the report root.
- Do not use legacy `<name>.Report/definition/definition.pbir` for enhanced PBIR.

Treat `ReportDefinition: Required artifact is missing`, `RequiredArtifactMissing: Path: definition.pbir`, and `RequiredArtifactMissing: ArtifactName: ReportDefinition` as validation failures.

## Platform metadata

Every `.platform` file in Report and SemanticModel artifact folders must:

- Parse as JSON.
- Include a supported Fabric git integration platform properties `$schema`.
- Include `config.version` as `"2.0"`.
- Include `config.logicalId` as a stable UUID string.

Treat `.platform` files with only `$schema` and metadata as invalid. Treat `ObjectNotPerSchema: Path: .platform` and "Required properties are missing from object: config" as validation failures.

## Report pages must contain visuals

Page metadata is not enough. Every page listed in `definition/pages/pages.json` must have a page folder, `page.json`, and at least one `visual.json` under that page.

Do not mark a Power BI report complete when:

- Only page shells exist.
- Only one page has visuals and the remaining planned pages are blank.
- The report has only key performance indicator cards and no slicers, trends, breakdowns, or details where the approved scope requires them.
- Markdown files describe pages but PBIR report definition files do not implement them.

When a user reports "blank pages", "no visuals", or "only key performance indicators", immediately audit visual counts per page, compare them to the approved page plan, add supported visuals, rerun validation, and tell the user to close Power BI Desktop without saving before reopening from disk.

## TMDL and partition syntax

- Do not put Markdown code fences inside `.tmdl` files.
- Power Query M must be placed in the valid TMDL expression or partition source syntax for the chosen format.
- Do not put bare Power Query M steps such as `AddedKey = Table.AddColumn(...)` at the root of `.tmdl` files.
- Indented `let ... in ...` partition expressions are allowed when they follow a known-good TMDL pattern.
- Unindented loose `let` or `in` lines are not allowed.
- For PostgreSQL imports, quote server and database parameters, hardcode the approved gold/mart schema in the source record, select only modeled columns, transform important types, and include the `PBI_ResultType = Table` annotation.

## Linguistic metadata content type

Do not generate linguistic metadata by default. If TMDL contains `LinguisticMetadata`, `culture`, `linguisticMetadata`, `content`, or content-type sections, the declared content type and actual content must match:

- XML content type requires valid XML.
- JSON content type requires valid JSON.
- JSON such as `{ "Version": "1.0.0" }` must never be written into XML-typed linguistic metadata.
- XML must never be written into JSON-typed linguistic metadata.

If the generator cannot guarantee correctness, omit linguistic metadata. Treat Power BI Desktop errors such as `does not comply with the Xml content-type` and `Data at the root level is invalid. Line 1, position 1` as validation failures.

## Report metadata

- `definition/report.json` must include `themeCollection.baseTheme.reportVersionAtImport` as a non-empty string.
- Default to `"5.55"` for the April 2026 Desktop format unless a known-good project reference proves another value.
- The SemanticModel should include the required model definition files for the selected format, such as `definition.pbism`, `database.tmdl`, `model.tmdl`, expressions, cultures, relationships, tables, and a calculated measures table when measures are generated.

## Consultant-grade content

The agent owns the first report design after the user approves the presentation layer. Do not wait for the user to list every visual.

Use the validated gold/mart model and analytics insight outputs to create:

- Executive overview with prioritized key performance indicators, primary slicers, at least one trend, and at least one business breakdown.
- Subject-area pages with key performance indicators, trends, breakdowns, and detail tables where supported.
- Trends page when usable fact dates exist.
- Report Information or Report Settings page with definitions, caveats, privacy handling, validation status, and open decisions.

Every planned page must either have real visuals or be explicitly deferred with the reason in `reports/agent/presentation_report.md`.

## Validation gate

Before handoff:

1. Run `python scripts/validate_powerbi_pbip.py <pbip_project_folder>`.
2. Record visual counts by page in `reports/agent/presentation_report.md`.
3. Run Power BI Modeling Model Context Protocol validation when available.
4. Run Power BI Desktop open validation when available.
5. Fix and repeat until validation passes, or mark the phase blocked with exact evidence.

Do not mark presentation delivery complete when the report has not been opened successfully and Desktop validation was available.
