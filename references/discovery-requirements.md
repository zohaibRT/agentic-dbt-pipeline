# Discovery & Requirements Checkpoint

Use this as the first phase for a new dbt project or full pipeline request.

## Goal

Analyze the available source schemas enough to orient the project and the data engineer before planning any build work.

This phase is read-only. Do not create dbt projects, install packages, run codegen, write model files, create warehouse schemas, or change profiles during discovery.

## Phase contract

| Area | Contract |
|---|---|
| Inputs required | Confirmed domain, dbt profile name, source schema, and selected adapter |
| Allowed changes | Discovery report, pipeline status, and context tree only after required inputs are valid |
| Not allowed | dbt project creation, package installation, codegen, model files, warehouse schema changes, profile changes, or alternate source profiling without approval |
| Commands to run | Lightweight metadata and profiling queries through the selected dbt profile adapter only |
| Completion criteria | Source inventory, relationships, business processes, data quality signals, recommended medallion direction, confidence, unknowns, and user decisions are documented |
| Report required | `reports/agent/discovery_report.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md` |

Do not assume the business domain. Even when the user provides a domain label, first understand the source evidence:

1. Source tables
2. Table relationships
3. Business processes
4. Metrics required
5. Data quality rules
6. Required output models
7. Reporting needs

Treat the domain label as context, not proof. If the source tables suggest a different business process than the label, report the mismatch and ask before modeling.

## Understanding gate

If the agent cannot properly understand or prove any of the seven required areas above, do not assume. Mark the item as unknown, explain why it matters, recommend the safest professional default when one exists, and ask the user for the missing business meaning or approval before designing dependent models, metrics, tests, semantic definitions, or presentation outputs.

The agent may continue only with independent safe work that does not depend on the unknown item. Any blocked or deferred scope must be listed in the discovery report, phase plan, phase report, pipeline status, and context tree.

Do not start discovery until the active `domain`, `dbt_profile_name`, and `source_schema` are confirmed from the current user prompt or a valid `.env`. If `.env` is missing or still contains placeholder values, follow [env-configuration.md](env-configuration.md) and stop for user input first. Do not inspect the repository, terminal output, other workspaces, prior workspaces, profile target schemas, warehouse schemas, or old runs to suggest or choose a source schema.

Before any source discovery, follow [warehouse-adapter-routing.md](warehouse-adapter-routing.md). Resolve the selected dbt profile adapter from `~/.dbt/profiles.yml`, announce the selected profile and adapter, and use only that adapter's metadata queries. Before this route is locked, do not call AWS, Redshift, PostgreSQL, Snowflake, BigQuery, Databricks, cloud identity checks, warehouse connectors, metadata queries, or Model Context Protocol discovery servers. If `.env` selects a PostgreSQL profile, use PostgreSQL discovery only. Do not call AWS, Redshift, or any other warehouse-specific connector unless the selected profile adapter is that warehouse type or the user explicitly changes profiles.

If the configured source is missing, empty, inaccessible, ambiguous, mismatched, or appears to be the wrong source, stop discovery and follow [source-confirmation.md](source-confirmation.md) plus the wrong-source checkpoint in [warehouse-adapter-routing.md](warehouse-adapter-routing.md). The agent may list candidate databases, datasets, catalogs, schemas, tables, tenants, clients, domains, environments, or table counts as metadata only, but must not profile candidate tables, infer business entities, draw diagrams, write discovery reports, update `.env`, or continue with a different source until the user approves the exact replacement.

Discovery is project-oriented, not setup-oriented. The discovery input, report, and chat output should focus on the source data and the future analytics project, not on environment setup, bootstrap, package installation, git, continuous integration, or agent configuration.

Discovery is also phased. Initial discovery should be lightweight and should not fully design every bronze, silver, gold, semantic, evaluator, and documentation artifact. See [phased-discovery.md](phased-discovery.md). Deeper discovery happens immediately before each layer/phase.

Discovery must include Mermaid diagrams when the source data has enough evidence to support them. Create an entity relationship diagram during discovery when any credible table relationships exist. Create other necessary Mermaid diagrams when they make the project easier to review, such as source inventory, candidate business process flow, or high-level medallion direction. Do not draw relationships or flows that are only guesses; list uncertain items as notes outside the diagram.

When discovery finds sensitive fields or ambiguous, placeholder, abbreviated, generic, or poorly named fields, read [privacy-and-unknown-fields.md](privacy-and-unknown-fields.md). Recommend a safe default in the discovery report instead of only asking what to do. For example, recommend excluding or masking direct identifiers from gold/marts by default, and recommend passing unclear source fields through bronze/staging as raw unmapped fields while excluding them from gold/marts until definitions are provided.

## Allowed read-only actions

- Load `.env` and non-secret config values
- Confirm the selected dbt profile name and adapter
- Run `dbt debug` only when a dbt project/profile already exists and the command is needed to verify read-only access
- Inspect source schemas, tables, columns, and row counts
- List candidate databases, datasets, catalogs, schemas, tables, tenants, clients, domains, environments, or table counts as metadata only when the confirmed source is missing, empty, or mismatched, then stop for user approval before profiling any candidate
- Check candidate primary keys, foreign keys, date columns, measures, status/code columns, and empty tables
- Inspect existing project files if the project already exists

## Discovery summary

After discovery, explain in Markdown:

- Project/domain being analyzed
- Source schemas/tables found and row counts
- Important entities and likely relationships
- Entity relationship diagram in Mermaid `erDiagram` when credible relationships are found
- Other necessary Mermaid diagrams, such as source inventory, business process flow, or high-level medallion direction, when they help the data engineer review the source
- Candidate business processes, such as appointments, encounters, claims, orders, tickets, or events
- Candidate facts, dimensions, and metrics implied by the source
- Required output models and reporting needs that are supported, unsupported, or still unclear
- Data quality rules discovered or recommended for the next phase
- Empty tables, suspicious columns, missing keys, date ranges, and data quality notes
- Privacy/sensitive-field observations
- Unknown coded fields, recommended default handling, and needed business definitions
- Recommended medallion direction for sources, bronze/staging, silver/intermediate, and gold/marts, without finalizing every model design
- Suggested business questions or analytics use cases the source appears able to support
- Agent recommendation with evidence
- What looks right for the next phase
- What is not ready yet
- What the agent is confident about
- What the agent is not confident about
- Required user decisions before modeling
- Next phase to discover/build first
- Mermaid visibility/parse verification for any diagram included

Put setup/config context at the end under a short `Inputs Used` section only:

- Domain
- dbt profile name, without credentials
- Adapter selected from the dbt profile
- Source schema
- Source tables inspected

Do not lead the discovery report with profile details, `.env` handling, package setup, bootstrap status, git status, virtual environment setup, continuous integration, or Agents Schema. Those belong in setup/bootstrap reports.

## Discovery files are required

Discovery must be written to files, not only posted in chat, but only after required inputs are confirmed.

If `.env` is missing, invalid, or contains placeholders, do not create or update discovery files. Do not create `reports/agent/discovery_report.md`, `reports/agent/PIPELINE_STATUS.md`, or `reports/agent/CONTEXT_TREE.md` for discovery until the user provides valid `DBT_DOMAIN`, `DBT_PROFILE_NAME`, and `DBT_SOURCE_SCHEMA`.

If the configured source is empty or the agent recommends a different database, dataset, catalog, schema, table, tenant, client, domain, environment, or assumption, do not create or update discovery files for the candidate source until the user approves that replacement.

Before sending the discovery summary in chat, create or update these files:

```text
reports/agent/discovery_report.md
reports/agent/PIPELINE_STATUS.md
reports/agent/CONTEXT_TREE.md
```

If the dbt project root does not exist yet, create `reports/agent/` in the current workspace/run root. Move or preserve these files in the dbt project root later only if the project root is created elsewhere and the user approves that layout.

The chat response should be a concise summary plus links/paths to these files. Do not use chat as the only discovery record.

## Required discovery diagrams

Add a `Diagrams` section to `reports/agent/discovery_report.md`.

Required:

- Mermaid entity relationship diagram using `erDiagram` when profiling, constraints, column naming, or user-approved rules reveal credible relationships.
- Mermaid source inventory or source relationship flow when the schema has multiple tables and the entity relationship diagram alone is not enough to explain the source shape.
- Mermaid high-level medallion direction diagram when the next recommended path would be clearer visually.

Optional:

- Candidate business process flow, such as appointment -> encounter -> claim, order -> shipment -> invoice, or ticket -> assignment -> resolution.
- Metric or semantic-layer concept diagram only when useful for the requirements conversation; do not finalize metric design during initial discovery.

For every discovery diagram:

- Use Mermaid only.
- Use full wording in titles and notes.
- Verify visibility or parse status with [mermaid-diagrams.md](mermaid-diagrams.md).
- Record the verification result in `reports/agent/discovery_report.md` and `reports/agent/CONTEXT_TREE.md`.
- Mark uncertain relationships as notes outside the diagram instead of drawing them as confirmed edges.

## Recommended medallion direction

Add a `Recommended Medallion Direction` section to `reports/agent/discovery_report.md`.

This section must cover the full path:

| Area | What to include |
|---|---|
| Sources | Source schemas, source tables, source naming, tables to include or ignore, and source tests/codegen direction |
| Bronze / staging | One source-shaped staging model per included table, expected grain, basic casts/renames, sensitive columns to pass, drop, or hold for approval |
| Silver / intermediate | Likely reusable joins, relationship checks, mapping needs, business flags, grain-preserving intermediate models, and items that need more discovery before joining |
| Gold / marts | Candidate facts, dimensions, reporting marts, metric areas, privacy exposure concerns, and final business approvals needed before building |

Use this template:

```markdown
## Recommended Medallion Direction

| Layer area | Recommendation | Evidence | Not ready yet | Approval needed |
|---|---|---|---|---|
| Sources | <source YAML and source table direction> | <tables, columns, profile evidence> | <missing/unclear source items> | <source exclusions or naming approvals> |
| Bronze / staging | <staging direction> | <grain, columns, data quality evidence> | <ambiguous columns or sensitive fields> | <privacy/pass-through approvals> |
| Silver / intermediate | <intermediate direction> | <relationship/cardinality evidence> | <joins, mappings, or empty tables needing more profiling> | <business rule approvals> |
| Gold / marts | <facts, dimensions, marts, and metrics direction> | <business processes and measures found> | <metric definitions or privacy decisions not proven> | <metric, grain, and exposure approvals> |
```

Keep this section directional during initial discovery. Do not list every final model as if it is approved. The goal is to help the data engineer understand the recommended path and decide whether to add requirements before build planning.

## Requirements checkpoint

Before automatic project setup and connection validation, ask whether the user wants to add or change requirements.

Use this wording:

```text
Discovery is complete. I have not built or changed anything yet.

Discovery route:
Using `.env` profile `<profile_name>` with adapter `<adapter_type>`. I did not query other warehouses.

Here is what I concluded from the source data:
<short Markdown summary>

My recommendation:
<recommended next step and why>

What looks right:
<safe or well-supported choices>

What is not ready yet:
<risks, missing data, ambiguous fields, or weak assumptions>

Confidence:
- Confident about: <validated source/project facts>
- Less confident about: <business meaning, privacy choices, metric dates, ambiguous fields, rebuild/refactor decisions, or anything not proven yet>

Needs your approval:
<business-impacting choices before the next build phase>

Before I run project setup and connection validation, do you want to add any requirements?
Examples: field mappings, coded-field definitions, columns to exclude, metric definitions, privacy rules, naming rules, facts/dimensions to prioritize, or tables to ignore.

Reply with your changes/requirements, or reply "continue" if you approve the recommendation and want me to run project setup and connection validation automatically.
```

If the user replies `continue`, `no changes`, `go ahead`, or similar, proceed to automatic project setup and connection validation in [bootstrap.md](bootstrap.md). Do not ask for a separate `approve bootstrap` response unless a setup safety gate is triggered.

If the user provides requirements, add them to the plan as `project_rules` and use them in later phases.

## Do not

- Treat discovery as approval to build.
- Ask for commit approval during discovery because no files should change.
- Skip the requirements checkpoint on a new full pipeline.
- Hide inferred business logic. Explain what was inferred and what still needs confirmation.
- Switch to a different database, dataset, catalog, schema, table, tenant, client, domain, environment, or assumption because it "looks likely" without user approval.
- Profile candidate tables or write discovery reports for a guessed replacement source before approval.

After discovery is summarized, confirm that `reports/agent/discovery_report.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md` were created or updated. Do not defer discovery files to project setup and initialization.
