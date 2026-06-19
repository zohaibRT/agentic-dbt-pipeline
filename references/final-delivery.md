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

Summarize:

- Files/layers created
- Build and docs results
- Project evaluator result
- Git commit status
- Agents Schema status
- Known data limitations
- Open user decisions
