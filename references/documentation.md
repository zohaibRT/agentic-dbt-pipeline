# Documentation Requirements

Apply when completing a model layer or `workflow_phase: docs`.

Also use dbt-labs skill: `using-dbt-for-analytics-engineering` -> `references/writing-documentation.md`.

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
      - name: customers
        description: One row per customer
```

## Source freshness *(optional)*

Add when the source has a reliable loaded-at column:

```yaml
    freshness:
      warn_after: {count: 24, period: hour}
      error_after: {count: 48, period: hour}
    loaded_at_field: updated_at
```

Only add if `updated_at` (or equivalent) exists in source YAML - **do not assume**.

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
