# Final Delivery Checklist

Use this before calling a dbt pipeline complete.

## Deliverables

- Source YAML generated from real source schema
- Discovery report file produced before build planning
- Staging, intermediate, and mart models built successfully
- Tests added for primary keys, relationships, accepted values, and mapping coverage where applicable
- Semantic layer or metrics added on final mart models when requested
- dbt documentation generated
- Project evaluator run and warnings summarized
- Presentation layer recommendation produced after final validation, with user-facing options and suggested metrics
- Agents Schema workflow prepared after `target/manifest.json` exists, when supported by the warehouse destination
- Continuous integration workflow prepared when GitHub automation is requested
- Commits created by phase
- `AGENT_PLAN.md` records approved phase plans and short phase results
- `reports/agent/` contains phase reports, `PIPELINE_STATUS.md`, and `CONTEXT_TREE.md`

## README or handoff notes

Update or create project handoff notes with:

- Domain and source schema used
- dbt profile name used, without secrets
- Layer names and physical schema naming
- Schema isolation status, including evaluator/seeds/snapshots schemas and whether source schema stayed clean
- Important source tables
- Source discovery conclusions and requirements captured before build
- Final facts, dimensions, marts, and metrics
- Presentation layer recommendation, including possible key performance indicators, semantic metrics, suggested report or dashboard pages, and query handoff options
- Known empty tables or data quality limitations
- Confidence notes: what was validated vs what still needs confirmation
- Mermaid diagrams created or updated, with visibility verification status
- Incremental, snapshot, exposure, and privacy decisions
- How to run `dbt build`, `dbt docs generate`, and `dbt docs serve`
- What still needs business review
- Which phase plans were approved before build
- Links to phase reports showing what was done, correct, warning, failed, and open
- Link to `reports/agent/CONTEXT_TREE.md` for reusable project context

## Final validation

Run:

```powershell
dbt parse --no-partial-parse
dbt build
dbt docs generate
```

If a full `dbt build` is too expensive, explain why and run the most complete safe build.

For local documentation viewing after `dbt docs generate`:

```powershell
dbt docs serve --host 127.0.0.1 --port 8080
```

If the agent starts docs serving, do it as a non-blocking/background process and report the URL.

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
| Evaluator schema | `<layer_schema_prefix>_evaluator` |
| Plan file | `AGENT_PLAN.md` |
| Phase reports | `reports/agent/` |
| Context tree | `reports/agent/CONTEXT_TREE.md` |
| Git | `<commit/push status>` |

### What changed

- Files/layers created
- Important models created by layer
- Semantic models and metrics added
- Presentation layer recommendation and whether the user approved any follow-up artifact
- Continuous integration or Agents Schema workflow changes
- Mermaid diagrams created or updated
- Documentation generated and documentation serve URL when started

### Validation results

- Build and documentation results
- Project evaluator result
- Schema isolation check result
- Key pass/warn/fail counts when available
- Phase plan approval status
- Phase report status and path
- Mermaid diagram visibility/parse status when diagrams were created or changed

### Data notes

- Source row counts and empty tables
- Known data quality limitations
- Important assumptions used
- Confidence: what is proven and what is uncertain
- PII/PHI or sensitive-field decisions

### Git and automation

- Git commit status
- Agents Schema status
- Continuous integration status

### Open decisions

- Open user decisions
- Whether to create a presentation layer artifact such as a business-facing report, dashboard design, semantic layer refinement, or query handoff
- Recommended next actions

Keep the final response readable for a new dbt user. Do not bury blockers, failed validation, unsupported Agents Schema destinations, or sensitive-data risks inside long prose.
