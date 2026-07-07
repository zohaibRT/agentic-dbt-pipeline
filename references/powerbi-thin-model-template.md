# Power BI Thin Model Template Workflow

Use this as the preferred Power BI workflow when the user explicitly chooses Power BI at the presentation decision gate.

This is the preferred Power BI path. The human uses Power BI Desktop to create the physical model and attach data. The agent creates the handoff folder/checklist, waits for the saved PBIP path, and then only injects approved reporting semantics such as DAX measures, descriptions, display folders, and harmless annotations.

## When To Use This

Use the thin model template workflow when:

- The user already has a PBIP that opens in Power BI Desktop.
- The user can create a base PBIP once from Power BI Desktop.
- The report must reuse authenticated local credentials or gateway-compatible connections.
- Previous generated PBIP files failed because of M code, schema, credential, relationship, culture, linguistic metadata, or Desktop-version issues.
- The physical gold tables, import partitions, date table, and relationships are already correct in the template.

Do not use this workflow to silently adapt a nearby local PBIP. The exact template path and what will be reused must be shown to the user and approved.

## Required Base Template

The base template should be created manually in Power BI Desktop or produced by an already validated template process.

It must contain:

- Approved source connections and import or DirectQuery partitions.
- Approved gold, mart, bridge, and date/time tables.
- Approved relationships with no ambiguous active paths.
- A dummy measures table such as `_KPI_Measures`, `_Measures`, or another user-approved name.
- Cached or gateway-compatible authentication handled by Power BI, not by files written by the agent.
- A PBIP project that opens successfully before the agent edits it.

The dummy measures table may be a calculated table such as:

```DAX
_KPI_Measures = ROW("Status", "Initialized")
```

## Human-Connected Template Checkpoint

When no approved PBIP template exists yet, do not continue by inventing database connections, Power Query M, relationships, visuals, or source partitions. Create a human handoff checkpoint instead.

The agent should:

1. Create the requested Power BI output folder.
2. State the exact `.pbip` path and filename the human should use.
3. List the recommended gold, mart, bridge, and date/time tables to connect.
4. List the required relationships and one-side uniqueness checks that were proven in dbt.
5. List the recommended import mode, DirectQuery mode, or composite mode with the reason.
6. Ask the user to open Power BI Desktop, connect the approved tables, confirm or create relationships, create the measures table, and save as PBIP at the specified path.
7. Ask for a simple confirmation with the PBIP path, such as `Connected and saved: <path>`.
8. Stop until the user confirms the template is ready and data is attached.

Use a native clickable question when available:

```text
Power BI needs a Desktop-created template before I inject measures.

I created the Power BI handoff folder and table checklist. Please open Power BI Desktop, connect the approved data, create the measures table, and save the PBIP at the specified path.

Is the PBIP created, saved, and connected to data?
```

Recommended options:

- `Yes - PBIP is saved and data is connected`
- `Use existing PBIP template path`
- `Skip Power BI for now`

After the user confirms the PBIP path, validate the template before editing it. If the template does not open, has missing tables, missing relationships, ambiguous relationships, no data connection, or no measures table, report the issue and ask for approval before changing it.

## Agent Scope

The agent may:

- Copy the approved template to the requested output location.
- Parse approved key performance indicator Markdown, semantic metrics, or explicit user requirements.
- Insert DAX measures only into the approved measures table.
- Add measure descriptions, format strings, display folders, and safe annotations.
- Update report pages only when the user explicitly approved report-page generation or editing after the Desktop-created template exists.
- Run static PBIP validation, Power BI Modeling Model Context Protocol validation, DAX smoke tests, and Desktop open validation when available.

The agent must not:

- Edit Power Query M, source partitions, connection strings, credentials, physical table names, or schema names.
- Add, remove, or rename physical imported tables unless the user explicitly approves that change.
- Change relationship paths unless the user approved relationship work and dbt cardinality proof exists.
- Create visuals or report pages by default; focus on measures, descriptions, display folders, and validation unless report editing is explicitly approved.
- Create business logic only in Power BI when it belongs in dbt.
- Mark presentation complete if the copied and modified PBIP was not validated.

## Injection Rules

1. Locate the approved measures table in TMDL files or `model.bim`.
2. If no measures table exists, pause and ask whether to create one or ask the user to add it in Desktop.
3. Keep the existing model format. Do not convert between TMDL and `model.bim` unless the user approves.
4. Inject only measures that are present in `KPI_DEFINITION_CONTRACTS.md`, `METRIC_VERIFICATION_MATRIX.md`, `kpi_catalog.md`, validated dbt semantic metrics, or user-approved requirements.
5. Preserve existing measures unless the user approved replacing them.
6. Use display folders from the key performance indicator catalog, dashboard specification, or semantic metric category.
7. Record every injected measure in `reports/agent/10_presentation/dax_measures.md`.
8. Record template path, copied output path, changed files, skipped measures, and validation evidence in `reports/agent/10_presentation/presentation_report.md`.

## Validation Gate

Before handoff, run and record:

- Template approval and source path.
- File tree validation.
- JSON parse validation for all JSON files.
- TMDL or `model.bim` structure validation.
- Confirmation that Power Query M, partitions, connection strings, and physical table objects were not changed.
- Relationship ambiguity audit.
- Power BI Modeling Model Context Protocol `ConnectFolder` validation when available.
- DAX smoke test when available.
- Power BI Desktop open validation when Desktop is available.

If any validation fails, fix and repeat. If Desktop or Model Context Protocol validation is unavailable, record `NOT RUN` with the exact reason and do not claim those checks passed.
