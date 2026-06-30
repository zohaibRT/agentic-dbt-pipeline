# Documentation Requirements

Apply when completing a model layer or `workflow_phase: docs`.

Also use dbt-labs skill: `using-dbt-for-analytics-engineering` -> `references/writing-documentation.md`.

Before docs-only work, write/update `AGENT_PLAN.md` with the docs plan and get approval.

## Phase contract

| Area | Contract |
|---|---|
| Inputs required | Approved documentation phase plan, built models, current YAML, model grains, tests, caveats, and source freshness evidence when available |
| Allowed changes | Model YAML, source YAML, exposures/metrics documentation when approved, docs report, and generated docs artifacts |
| Not allowed | Business logic changes, model rewrites, unapproved source freshness fields, dashboards, or presentation artifacts |
| Commands to run | `dbt parse --no-partial-parse`, `dbt docs generate`, and optional non-blocking `dbt docs serve` when useful |
| Completion criteria | Model/source documentation is useful, generated documentation artifacts exist, and any missing docs are reported |
| Report required | `reports/agent/docs_report.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md` |

## Handoff to analytics insight reporting

Documentation completion does not close a full pipeline. After `dbt docs generate` passes in a full pipeline, the agent must read [analytics-insight-reporting.md](analytics-insight-reporting.md), write/update `AGENT_PLAN.md`, get approval, and run the analytics insight reporting phase before presentation work.

Set delivery status to `Documentation complete - analytics insight reporting pending`, not `Delivery complete`, until analytics insight reporting completes and the presentation-layer gate is reached.

Do not skip directly to [presentation-layer.md](presentation-layer.md) from documentation unless the user explicitly runs `workflow_phase: presentation_layer` after analytics insight reporting outputs already exist and are validated.

## Per-model YAML

For each model in staging, intermediate, and marts:

- `description` - purpose and grain (not just restating the model name)
- Column `description` for primary keys, foreign keys, and business fields
- Document non-obvious logic (e.g. `channel_id = -1` for unattributed)

## Per-source YAML

After codegen, add if missing:

```yaml
sources:
  - name: <source.name>
    description: Source tables for <domain>
    schema: <source.schema>
    tables:
      - name: <source_table>
        description: One row per <source_table_grain>
```

## Source freshness *(optional)*

Add when the source has a reliable loaded-at column such as `_etl_loaded_at`, `updated_at`, or an approved equivalent:

```yaml
    freshness:
      warn_after: {count: 24, period: hour}
      error_after: {count: 48, period: hour}
    loaded_at_field: updated_at
```

Only add if the loaded-at field exists in source YAML and reflects source load recency - **do not assume**.

Default source freshness:

- `warn_after: {count: 24, period: hour}`
- `error_after: {count: 48, period: hour}`

## Generate docs

Run after `dbt build` succeeds, or during `workflow_phase: docs`.

```powershell
$dbt = "dbt"
& $dbt docs generate
```

Verify `target/manifest.json` and `target/catalog.json`.

## Serve docs locally

Use this when the user wants to view docs locally or the run is an interactive local session.

```powershell
$dbt = "dbt"
& $dbt docs serve --host 127.0.0.1 --port 8080
```

`dbt docs serve` is a long-running local web server. If the agent starts it, run it as a non-blocking/background process, use the configured host/port from `project.config.yml`, and provide the URL:

```text
http://127.0.0.1:8080
```

If port `8080` is busy, try the next available port and report the final URL. Do not treat `docs serve` as required validation; `docs generate` is the required validation step.

## Commit

After docs YAML updates:

```powershell
git add models/
git commit -m "Add dbt tests and documentation"
```

Ask user before commit (default `commit: ask`).
