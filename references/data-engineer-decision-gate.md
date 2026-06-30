# Data Engineer Decision Gate

Use this before approving any phase plan that designs sources, models, tests, metrics, docs, or warehouse behavior.

## Core rule

The agent must make explicit data-engineering decisions before building. Do not leave design choices as hidden agent assumptions.

If the source data does not prove a decision and the choice affects business meaning, privacy, correctness, cost, or downstream usability, recommend the safest professional default first, then ask the user to approve or override it before building.

## Required decision checks

Every build-phase plan must include these checks when relevant:

| Check | What the agent must decide or ask |
|---|---|
| Source boundary | Which schemas/tables are read-only inputs, and which tables are excluded |
| Project shape | Project/root name, project slug, folders, source name, and schema prefix derived from source/project signals; domain is business context and only a last fallback |
| Grain | One clear grain for each planned model |
| Keys | Candidate primary keys, uniqueness/null checks, and safe surrogate keys when needed |
| Joins | Join keys, expected cardinality, and whether joins can multiply rows |
| Layer responsibility | What belongs in staging vs intermediate vs marts |
| Mapping | Whether codes/statuses need mapping seeds, reference joins, or user-provided definitions |
| Metrics | Metric definition, grain, filters, numerator/denominator, and semantic-layer target |
| Key performance indicators | Business meaning, source model, grain, numerator, denominator, filters, time field, dimensions, caveats, validation evidence, and approval status |
| Privacy | Direct identifiers, personally identifiable information, protected health information, sensitive fields, and whether they may reach marts |
| History | Whether snapshots or slowly changing dimensions are needed |
| Incremental strategy | Unique key, update timestamp/filter, late-arriving-data assumption, and full-refresh risk |
| Tests | Primary key, relationship, accepted value, not-null, and business-rule tests |
| Documentation | Model purpose, grain, important columns, assumptions, and limitations |
| Performance | Materialization choice, expected row volume, indexes/sort/cluster hints when relevant |
| Package outputs | Package/evaluator/audit outputs routed outside source schema |
| Validation | Exact dbt commands and data checks to prove the phase worked |
| Rollback/commit | Files and warehouse objects covered by the phase commit |

## Ask instead of guessing

Stop and ask when:

- Source tables, relationships, business processes, required metrics, data quality rules, required output models, or reporting needs are unclear and the uncertainty affects source design, model design, tests, metrics, semantic definitions, documentation, or presentation outputs.
- A metric can be defined more than one reasonable way.
- A key performance indicator lacks a clear numerator, denominator, filter, time field, source model, or caveat.
- A join can change the row count or double-count facts.
- A source column looks sensitive or unclear.
- A code/status mapping is incomplete or business-specific.
- A table is empty but important to the intended marts.
- The profile default schema equals the source schema.
- Multiple existing medallion schema prefixes exist.
- Incremental logic needs a timestamp or unique key that is not reliable.
- A package would create objects in the source schema.
- A phase plan changes after approval in a meaningful way.

## Acceptable inference

The agent may infer simple technical defaults when they do not change business meaning:

- Standard dbt folder names from configured layer names.
- Source name from source schema; domain only as a last fallback when source schema is generic.
- Project name and project slug from source/project signals; domain only as a last fallback.
- Basic casts, trimming, and column renames in staging.
- Generic tests for obvious primary keys when the data confirms uniqueness and non-nullness.
- Schema prefix from approved existing medallion schemas, source schema, project slug, or descriptive source name when there is no conflict; domain only as a last fallback.

Document inferred choices in the phase plan and phase report.

## Required recommendations for sensitive or unclear fields

Read [privacy-and-unknown-fields.md](privacy-and-unknown-fields.md) when direct identifiers, sensitive fields, protected health information, personally identifiable information, or unclear coded fields appear.

Default recommendation:

- Keep sensitive and unclear fields source-shaped in bronze/staging when needed for traceability.
- Do not expose clear-text direct identifiers in gold/marts unless the user approves.
- Do not rename or map unclear coded fields unless a reliable definition exists.
- Treat user approval to analyze or suggest names for unclear fields as discovery approval only, not implementation approval.
- Rename unclear fields only after the user approves the exact final column names.
- Exclude unclear coded fields from gold/marts by default, or keep them only as explicitly approved raw audit fields.

The agent should ask the user to approve this recommendation or provide definitions. Do not simply ask "what should I do?" without a recommended path.

## Phase plan section

Add this section to every phase plan:

```markdown
### Data Engineer Decision Check
| Decision | Choice | Evidence | Needs User Approval? |
|---|---|---|---|
| Grain | <one row per ...> | <source/profile evidence> | <yes/no> |
| Keys | <key columns/tests> | <uniqueness/null checks> | <yes/no> |
| Joins | <join/cardinality plan> | <relationship/profile evidence> | <yes/no> |
| Privacy | <include/exclude/mask fields> | <column names/rules> | <yes/no> |
| Materialization | <view/table/incremental> | <volume/use case> | <yes/no> |
| Key performance indicators | <metric definitions or deferred> | <gold/semantic evidence> | <yes/no> |
```

If there is nothing relevant for a decision, write `not applicable` rather than omitting the decision silently.

## Phase report section

Each phase report must include:

- Which data-engineering decisions were implemented.
- Which decisions were inferred and why they were safe.
- Which decisions remain open for the user.
- Any validation that contradicted the original plan.
