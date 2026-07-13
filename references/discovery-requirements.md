# Discovery & Requirements Checkpoint

Use this as the first phase for a new dbt project or full pipeline request.

## Goal

Analyze the available source schemas enough to orient the project and the data engineer before planning any build work.

This phase is read-only. Do not create dbt projects, install packages, run codegen, write model files, create warehouse schemas, or change profiles during discovery.

Read [discovery-artifacts.md](discovery-artifacts.md) and [discovery-status-vocabulary.md](discovery-status-vocabulary.md) before writing discovery outputs. Every discovery file must use the shared status vocabulary. Explain `WARN` with a reason; do not use `WARN` to hide `FAIL`.

## Phase contract

| Area | Contract |
|---|---|
| Inputs required | Confirmed domain, dbt profile name, source schema, and selected adapter |
| Allowed changes | Discovery report, requirements file, pipeline status, and context tree only after required inputs are valid |
| Not allowed | dbt project creation, package installation, codegen, model files, warehouse schema changes, profile changes, or alternate source profiling without approval |
| Commands to run | Lightweight metadata and profiling queries through the selected dbt profile adapter only |
| Completion criteria | Source inventory, relationships, business processes, data quality signals, inferred requirements, recommended medallion direction, confidence, unknowns, user decisions, reusable SQL proof files, `core_profile.json`, and `discovery_raw.json` are documented |
| Report required | `reports/agent/00_discovery/README.md`, `reports/agent/00_discovery/core_profile.json`, `reports/agent/00_discovery/discovery_raw.json`, `reports/agent/00_discovery/discovery_report.md`, `reports/agent/00_discovery/requirements.md`, `reports/agent/00_discovery/cardinality_report.md`, `reports/agent/00_discovery/relationship_profile.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md` |

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

Discovery is project-oriented, not setup-oriented. The discovery input, report, and chat output should focus on the source data and the future analytics project, not on environment setup, package installation, git, continuous integration, or agent configuration.

Discovery is also phased. Initial discovery should be lightweight and should not fully design every bronze, silver, gold, semantic, evaluator, and documentation artifact. See [phased-discovery.md](phased-discovery.md). Deeper discovery happens immediately before each layer/phase.

Discovery must include Mermaid diagrams when the source data has enough evidence to support them. Create an entity relationship diagram during discovery when any credible table relationships exist. Create other necessary Mermaid diagrams when they make the project easier to review, such as source inventory, candidate business process flow, or high-level medallion direction. Do not draw relationships or flows that are only guesses; list uncertain items as notes outside the diagram.

Discovery must also create reusable SQL proof files under `reports/agent/00_discovery/sql_proofs/` for the source-level evidence used in the discovery report. Follow the SQL proof standard in [report-artifact-organization.md](report-artifact-organization.md).

When discovery finds sensitive fields or ambiguous, placeholder, abbreviated, generic, or poorly named fields, read [privacy-and-unknown-fields.md](privacy-and-unknown-fields.md). Recommend a safe default in the discovery report instead of only asking what to do. For example, recommend excluding or masking direct identifiers from gold/marts by default, and recommend passing unclear source fields through bronze/staging as raw unmapped fields while excluding them from gold/marts until definitions are provided.

## Allowed read-only actions

- Load `.env` and non-secret config values
- Confirm the selected dbt profile name and adapter
- Run `dbt debug` only when a dbt project/profile already exists and the command is needed to verify read-only access
- Inspect source schemas, tables, columns, and row counts
- List candidate databases, datasets, catalogs, schemas, tables, tenants, clients, domains, environments, or table counts as metadata only when the confirmed source is missing, empty, or mismatched, then stop for user approval before profiling any candidate
- Check candidate primary keys, foreign keys, date columns, measures, status/code columns, and empty tables
- Check relationship cardinality, likely table grain, duplicate keys, null keys, match rates, many-to-many risks, and tables that should not be joined directly without aggregation
- Inspect existing project files if the project already exists

## Discovery SQL proofs

Create source proof queries for as much safe evidence as the source supports. Do not only capture row counts in prose.

At minimum, create:

| Proof type | Required when | Example filename |
|---|---|---|
| Source table inventory | Always after source schema is confirmed | `001_source_table_inventory.sql` |
| Per-table row count | Every **included** source table, or priority tables when the schema is very large | `010_<source_table>_row_count.sql` |
| Candidate key check | A likely primary key or unique business key exists | `020_<source_table>_<key>_key_check.sql` |
| Status/category distribution | Status, stage, type, category, channel, source system, active flag, or similar fields exist | `030_<source_table>_<column>_distribution.sql` |
| Active/open/closed count | Any active, current, open, closed, completed, cancelled, deleted, status, or lifecycle field exists | `035_<source_table>_<business_state>_count.sql` |
| Date coverage | Date/time columns exist | `040_<source_table>_<date_column>_date_coverage.sql` |
| Amount/quantity summary | Amount, balance, cost, price, fee, quantity, duration, count, area, capacity, or similar numeric fields exist | `050_<source_table>_<measure>_summary.sql` |
| Relationship candidate proof | Candidate foreign key relationship exists | `060_<child_table>_<parent_table>_relationship_check.sql` |
| Bridge or many-to-many check | Link/bridge-like tables or many-to-many risk exists | `070_<table>_bridge_or_cardinality_check.sql` |
| Data quality signal | Nulls, duplicates, invalid codes, stale data, or empty tables matter | `080_<source_table>_data_quality_check.sql` |

Each proof file must include the captured result in the comment header above the runnable SQL. For example, if the source has an account table with status or active columns, write the query that proves active account counts and include the captured active count in the file header.

The discovery report must include a `SQL Proof Files` section with links/paths and one-line explanations. The chat summary should mention the most important source proofs, such as table counts, active/open counts, date coverage, and relationship evidence.

## Large source schemas

When the source schema has hundreds or thousands of tables:

1. Always create `001_source_table_inventory.sql` with all table names and row counts.
2. Always populate `discovery_raw.json.tables[]` with at least `table_name`, `row_count`, `inclusion_status`, and `inclusion_reason` for every table.
3. Apply [table-inclusion-priority-filter.md](table-inclusion-priority-filter.md) to choose included, deferred, and excluded tables.
4. Mark tables as `included`, `deferred`, or `excluded` in `discovery_report.md` and `requirements.md`.
5. Create deep per-table SQL proofs only for included or priority tables.
6. Do not create thousands of `010+` row-count proof files.
7. Add a **Table Inclusion Filter** section to `discovery_report.md` with process name, counts, and rationale.

Document the scope decision in `discovery_raw.json.scope.notes`.

### Priority filter quick rule

```text
Inventory all tables (001)
  -> name the first-pass business process
  -> keep fact/event tables on that process
  -> keep related dimensions/lookups
  -> exclude audit/log/platform/empty (unless requested)
  -> require inclusion_reason for every table
  -> ask user if process scope is unclear
  -> deep-proof only the included set (010+)
```

Every inclusion decision must be visible in `discovery_raw.json` and the discovery report. Do not leave filter logic only in chat.

## Mandatory JSON artifacts

Discovery must create or fully update these JSON files every run:

| File | Required | Purpose |
|---|---|---|
| `reports/agent/00_discovery/core_profile.json` | Yes | Non-secret profile/source/workspace snapshot for reload without chat |
| `reports/agent/00_discovery/discovery_raw.json` | Yes | Structured warehouse evidence and proof linkage |

Start from:

```text
templates/reports/00_discovery/core_profile.json
templates/reports/00_discovery/discovery_raw.json
```

Rules:

- Keep the top-level `_file_meta` object and explain any status used.
- Never store passwords, tokens, private keys, or row-level direct identifiers.
- Replace all placeholder values with real discovery evidence.
- Link `discovery_raw.json.queries_executed[]` to `sql_proofs/` files.
- For large schemas, shallow table entries are allowed for deferred/excluded tables; included tables need richer column/key/relationship detail.

## Discovery summary

After discovery, explain in Markdown:

- Project/domain being analyzed
- Source schemas/tables found and row counts
- Important entities and likely relationships
- Cardinality, relationship profile, likely grains, duplicate/null key risks, and many-to-many or bridge-table candidates
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

Do not lead the discovery report with profile details, `.env` handling, package setup, setup status, git status, virtual environment setup, continuous integration, or Agents Schema. Those belong in setup reports.

## Discovery files are required

Discovery must be written to files, not only posted in chat, but only after required inputs are confirmed.

If `.env` is missing, invalid, or contains placeholders, do not create or update discovery files. Do not create `reports/agent/00_discovery/discovery_report.md`, `reports/agent/00_discovery/requirements.md`, `reports/agent/PIPELINE_STATUS.md`, or `reports/agent/CONTEXT_TREE.md` for discovery until the user provides valid `DBT_DOMAIN`, `DBT_PROFILE_NAME`, and `DBT_SOURCE_SCHEMA`.

If the configured source is empty or the agent recommends a different database, dataset, catalog, schema, table, tenant, client, domain, environment, or assumption, do not create or update discovery files for the candidate source until the user approves that replacement.

Before sending the discovery summary in chat, create or update these files:

```text
reports/agent/00_discovery/README.md
reports/agent/00_discovery/core_profile.json
reports/agent/00_discovery/discovery_raw.json
reports/agent/00_discovery/discovery_report.md
reports/agent/00_discovery/requirements.md
reports/agent/00_discovery/cardinality_report.md
reports/agent/00_discovery/relationship_profile.md
reports/agent/00_discovery/sql_proofs/
reports/agent/PIPELINE_STATUS.md
reports/agent/CONTEXT_TREE.md
reports/agent/REPORT_INDEX.md
reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md
```

`core_profile.json` and `discovery_raw.json` are mandatory on every discovery run. Do not treat them as optional agent-created extras.

Use these canonical discovery templates when creating the discovery files:

| Output | Template |
|---|---|
| `reports/agent/00_discovery/README.md` | `templates/reports/00_discovery/README.md` |
| `reports/agent/00_discovery/core_profile.json` | `templates/reports/00_discovery/core_profile.json` |
| `reports/agent/00_discovery/discovery_raw.json` | `templates/reports/00_discovery/discovery_raw.json` |
| `reports/agent/00_discovery/first_pass_scope.json` | `templates/reports/00_discovery/first_pass_scope.json` |
| `reports/agent/00_discovery/discovery_report.md` | `templates/reports/00_discovery/discovery_report.md` |
| `reports/agent/00_discovery/requirements.md` | `templates/reports/00_discovery/requirements.md` |
| `reports/agent/00_discovery/cardinality_report.md` | `templates/reports/00_discovery/cardinality_report.md` |
| `reports/agent/00_discovery/relationship_profile.md` | `templates/reports/00_discovery/relationship_profile.md` |
| `reports/agent/00_discovery/DISCOVERY_APPROVAL_CHECKLIST.md` | `templates/reports/00_discovery/DISCOVERY_APPROVAL_CHECKLIST.md` |
| `reports/agent/00_discovery/sql_proofs/_proof_index.md` | `templates/reports/00_discovery/sql_proofs/_proof_index.md` |
| Individual SQL proof files | `templates/reports/00_discovery/sql_proofs/sql_proof_template.sql` |
| `reports/agent/PIPELINE_STATUS.md` | `templates/reports/root/PIPELINE_STATUS.md` |
| `reports/agent/CONTEXT_TREE.md` | `templates/reports/root/CONTEXT_TREE.md` |
| `reports/agent/REPORT_INDEX.md` | `templates/reports/root/REPORT_INDEX.md` |
| `reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md` | `templates/reports/root/REQUIREMENTS_TRACEABILITY_MATRIX.md` |
| `reports/agent/NEXT_PHASE_PROMPT.md` | `templates/reports/root/NEXT_PHASE_PROMPT.md` |

Copy `PIPELINE_STATUS.md` from the template. Keep the Status Review Queue columns exactly, including **Why this status was used**. Do not shorten that table. See [discovery-status-vocabulary.md](discovery-status-vocabulary.md).

The templates define structure only. The content must change based on the confirmed source schema, source tables, row counts, keys, relationships, data quality, privacy findings, business process evidence, and user-provided rules.

If the dbt project root does not exist yet, create `reports/agent/` in the current workspace/run root. Move or preserve these files in the dbt project root later only if the project root is created elsewhere and the user approves that layout.

The chat response should be a concise summary plus links/paths to these files. Do not use chat as the only discovery record.

## Requirements file

Create `reports/agent/00_discovery/requirements.md` during discovery. This file is the project-facing requirements checkpoint extracted from the source schema, source data, domain label, and any user-provided rules. It must be easy for a data engineer to review before build planning.

Use the canonical template:

```text
templates/reports/00_discovery/requirements.md
```

Copy or recreate that template structure after required inputs are confirmed, then replace placeholders with source-specific evidence. Do not remove sections; write `None`, `Not observed`, or `Blocked` when a section has no evidence yet.

The required structure is:

```markdown
# Project Requirements From Discovery

## Inputs Used

- Domain: <domain>
- dbt profile name: <profile name without secrets>
- Adapter: <adapter>
- Source schema: <source schema>
- Source tables inspected: <tables>

## Source-Derived Requirements

| Area | Requirement inferred | Evidence | Confidence | Build impact |
|---|---|---|---|---|
| Source inclusion | <include/exclude direction> | <tables, row counts, relationships> | <high/medium/low> | <source YAML, staging, tests> |
| Business process | <process supported by data> | <entity flow evidence> | <high/medium/low> | <facts/intermediate direction> |
| Data quality | <tests or checks needed> | <keys, statuses, dates, nulls> | <high/medium/low> | <dbt tests and validation queries> |
| Privacy | <safe default> | <sensitive fields found> | <high/medium/low> | <gold/marts exposure rules> |
| Metrics | <candidate metric area> | <amount/status/date columns> | <high/medium/low> | <semantic layer/gold marts> |
| Reporting | <likely reporting need> | <final consumers implied by source> | <high/medium/low> | <presentation layer options> |

## Recommended Defaults

- <safe professional default derived from evidence>

## Open Questions For The Data Engineer

- <question that affects business meaning, privacy, metrics, grain, mappings, joins, or reporting>

## Deferred Or Blocked Scope

- <scope that should not be built until requirements are confirmed>

## User Requirements Captured

- <requirements already provided by the user, or "None yet">
```

Do not put environment setup instructions, package installation, git details, or agent configuration into `requirements.md`. Keep it focused on business and data requirements. Requirements may be inferred, but each inferred requirement must include evidence and confidence. If confidence is low or business meaning is not proven, phrase it as a recommended default or open question, not as an approved requirement.

## Required discovery diagrams

Add a `Diagrams` section to `reports/agent/00_discovery/discovery_report.md`.

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
- Record the verification result in `reports/agent/00_discovery/discovery_report.md` and `reports/agent/CONTEXT_TREE.md`.
- Mark uncertain relationships as notes outside the diagram instead of drawing them as confirmed edges.

## Recommended medallion direction

Add a `Recommended Medallion Direction` section to `reports/agent/00_discovery/discovery_report.md`.

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

## Discovery chat summary and requirements checkpoint

Before asking the requirements checkpoint question, send a normal assistant chat message with a visible Markdown summary. The native clickable question is only the approval control. It must not be the only place where the discovery results appear.

Use this visible chat shape:

```markdown
## Discovery Complete

Status: <PASS | WARN | BLOCKED>

Source reviewed:
- Profile: <profile name>
- Adapter: <adapter>
- Database or catalog: <database/catalog/project>
- Source schema: <source schema>
- Tables profiled: <count>
- Non-empty tables: <count>

Key findings:
- <business process/entity finding with evidence>
- <relationship/cardinality finding with evidence>
- <data quality, privacy, or unknown-field finding>

Validation and SQL proofs:
- <important proof result, such as row counts, key checks, relationship checks, active/open counts, or date coverage>
- SQL proof folder: `reports/agent/00_discovery/sql_proofs/`

Reports written:
- `reports/agent/00_discovery/discovery_report.md`
- `reports/agent/00_discovery/requirements.md`
- `reports/agent/00_discovery/DISCOVERY_APPROVAL_CHECKLIST.md`
- `reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md`
- `reports/agent/PIPELINE_STATUS.md`
- `reports/agent/CONTEXT_TREE.md`

Open decisions:
- <decision or "None blocking automatic setup">

Recommended next step:
- Run automatic project setup and configuration only.

Next step includes:
- dbt project scaffold or setup validation, dependencies, `dbt debug`, `dbt deps`, and `dbt parse`.

Next step does not include:
- Source YAML generation, bronze/staging, silver/intermediate, gold/marts, semantic layer, analytics insight reporting, presentation layer, commits, pushes, or source switching.

How to approve:
Use the clickable question below and choose **Yes, continue to setup**, or choose **Add requirements first** / **Tell me what to change**.
```

After that visible chat message, ask a short native question only when the normal Markdown summary remains visibly present directly above the question:

```text
Do you approve this discovery scope and want automatic project setup to run next?
```

Recommended options:

- `Yes, continue to setup`
- `Add requirements first`
- `Tell me what to change`

Do not put long findings, table lists, Mermaid diagrams, report links, or SQL proof details only in the native question. Those belong in the normal chat message and report files. Do not use the native question if the user would see only a question card, file diff, blank gap, or hidden summary above it.

If native interactive questions are unavailable, or the runtime cannot guarantee the visible Markdown summary directly above the question, use this text fallback:

```text
Do you approve this discovery scope and want automatic project setup to run next? Reply Yes to continue, or tell me what to change.
```

## Requirements checkpoint

Before automatic project setup and configuration, ask whether the user wants to add or change requirements.

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

Before I run project setup and configuration, do you want to add any requirements?
Examples: field mappings, coded-field definitions, columns to exclude, metric definitions, privacy rules, naming rules, facts/dimensions to prioritize, or tables to ignore.

Reply with your changes/requirements, or reply "continue" if you approve the recommendation and want me to run project setup and configuration automatically.
```

If the user replies `continue`, `no changes`, `go ahead`, or similar, proceed to automatic project setup and configuration in [bootstrap.md](bootstrap.md). Do not ask for a separate setup approval response unless a setup safety gate is triggered.

If the user provides requirements, add them to the plan as `project_rules` and use them in later phases.

## Do not

- Treat discovery as approval to build.
- Ask for commit approval during discovery unless the user explicitly wants to commit report artifacts; discovery may write report files but must not change source models, warehouse objects, profiles, packages, or project setup.
- Skip the requirements checkpoint on a new full pipeline.
- Hide inferred business logic. Explain what was inferred and what still needs confirmation.
- Switch to a different database, dataset, catalog, schema, table, tenant, client, domain, environment, or assumption because it "looks likely" without user approval.
- Profile candidate tables or write discovery reports for a guessed replacement source before approval.

After discovery is summarized, confirm that `reports/agent/00_discovery/discovery_report.md`, `reports/agent/00_discovery/requirements.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md` were created or updated. Do not defer discovery files to project setup and initialization.
