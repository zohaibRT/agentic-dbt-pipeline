# Final Delivery Checklist

Use this before calling a dbt pipeline complete.

## Deliverables

- Source YAML generated from real source schema
- Staging, intermediate, and mart models built successfully
- Tests added for primary keys, relationships, accepted values, and mapping coverage where applicable
- Semantic layer or metrics added on final mart models when requested
- dbt docs generated
- Project evaluator run and warnings summarized
- Agents Schema workflow prepared after `target/manifest.json` exists, when supported by the warehouse destination
- CI workflow prepared when GitHub automation is requested
- Commits created by phase

## README or handoff notes

Update or create project handoff notes with:

- Domain and source schema used
- dbt profile name used, without secrets
- Layer names and physical schema naming
- Important source tables
- Final facts, dimensions, marts, and metrics
- Known empty tables or data quality limitations
- Incremental, snapshot, exposure, and privacy decisions
- How to run `dbt build` and `dbt docs generate`
- What still needs business review

## Final validation

Run:

```powershell
dbt parse --no-partial-parse
dbt build
dbt docs generate
```

If a full `dbt build` is too expensive, explain why and run the most complete safe build.

## Final response

Always start with a concise user-facing summary before detailed handoff notes.

Use this order:

### Short summary

In 3-6 lines, say:

- Whether the pipeline or requested phase completed successfully
- What domain/source was used
- Which layers/models were created or changed
- Whether validation passed
- Whether anything important still needs user review

### Results

Use a compact table when helpful:

| Area | Result |
|---|---|
| Project | `<dbt_project_name>` in `<dbt_project_root>` |
| Profile | `<dbt_profile_name>` |
| Domain | `<domain>` |
| Source | `<source_schema>` / `<source_name>` |
| Layers | `<layer_1>` -> `<layer_2>` -> `<layer_3>` |
| Schemas | `<schema_1>`, `<schema_2>`, `<schema_3>` |
| Git | `<commit/push status>` |

### What changed

- Files/layers created
- Important models created by layer
- Semantic models and metrics added
- CI or Agents Schema workflow changes

### Validation results

- Build and docs results
- Project evaluator result
- Key pass/warn/fail counts when available

### Data notes

- Source row counts and empty tables
- Known data quality limitations
- Important assumptions used
- PII/PHI or sensitive-field decisions

### Git and automation

- Git commit status
- Agents Schema status
- CI status

### Open decisions

- Open user decisions
- Recommended next actions

Keep the final response readable for a new dbt user. Do not bury blockers, failed validation, unsupported Agents Schema destinations, or sensitive-data risks inside long prose.
