# dbt Analytics Engineer Prompt

Install once:

```bash
npx skills add zohaibRT/agentic-dbt-pipeline
```

Create `.env` from `.env.example` and fill the project settings there. Then use this prompt.

## Recommended Prompt

```text
Use the dbt Analytics Engineer skill (`agentic-dbt-pipeline`).

Act as a Principal Data Engineer. Design the dbt project to be modular, idempotent, scalable, testable, cost-efficient, and safe for downstream consumers. Treat data asset development like software engineering.

Build the dbt project using the settings from `.env`.
Run the full pipeline from source discovery through final delivery.

Read any project knowledge files I provide, such as `AGENT_KNOWLEDGE.md`, `docs/dbt_knowledge.md`, `docs/business_rules.md`, `.agents/project_knowledge.md`, and `reports/agent/CONTEXT_TREE.md`. Apply `project_rules` from my prompt first, summarize which knowledge was used in each phase plan/report, and ask before persisting new dbt knowledge from chat into project files.

Use the skill's built-in knowledge layer for reusable dbt, big data, warehouse optimization, semantic layer, Power BI, privacy, and validation standards. Use project knowledge only for local/domain overrides. Do not copy large external documentation into the project; use official documentation only when current version-specific behavior is needed.

If `.env` is missing, create it safely from `.env.example` with placeholder values only, ask me which dbt profile this pipeline should use by listing available profiles from `~/.dbt/profiles.yml` with profile name, adapter, database or database-equivalent, and profile schema, stop before discovery or dbt commands, and ask me for DBT_DOMAIN, DBT_PROFILE_NAME, and DBT_SOURCE_SCHEMA. Do not create discovery reports while `.env` is missing or placeholder-only. Do not fill `.env` from a profile, profile target schema, warehouse schema, previous run, example, or guess. Do not say you will resolve the active profile or run PostgreSQL, Redshift, Snowflake, BigQuery, Databricks, or any adapter-specific discovery until I choose `DBT_PROFILE_NAME`. Do not search the repository, inspect terminal output, infer, suggest, or summarize values from other workspaces or previous runs. Do not choose a profile automatically.

First, perform lightweight read-only project discovery only: inspect source schemas/tables, write `reports/agent/discovery_report.md`, update `reports/agent/PIPELINE_STATUS.md` and `reports/agent/CONTEXT_TREE.md`, summarize what you conclude about the data project, and ask whether I want to add requirements. Before discovery, resolve the active dbt profile from `.env`, read that profile's adapter from `~/.dbt/profiles.yml`, announce the selected profile and adapter, and use only that adapter's discovery path. Do not call AWS, Redshift, PostgreSQL, Snowflake, BigQuery, Databricks, cloud identity checks, warehouse connectors, metadata queries, or Model Context Protocol discovery servers before `.env` and the selected dbt profile adapter are resolved. Do not query AWS, Redshift, or any other warehouse unless the selected dbt profile uses that adapter or I explicitly ask you to change profiles. If the configured source is missing, empty, inaccessible, ambiguous, mismatched, or appears wrong, stop after metadata-only candidate listing, recommend the likely replacement with evidence, and wait for my approval before changing database, dataset, catalog, schema, table, tenant, client, domain, environment, assumption, `.env`, profile settings, profiling candidate tables, writing discovery reports, or continuing discovery. Keep discovery output focused on source data, entities, relationships, data quality, candidate models/metrics, and open modeling decisions; keep setup details out of the discovery summary except for a short inputs-used note. Include a `Recommended Medallion Direction` section that covers sources, bronze/staging, silver/intermediate, and gold/marts with recommendation, evidence, not-ready items, and approval needs for each area. During discovery, create a Mermaid entity relationship diagram when credible relationships exist, and create any other necessary Mermaid diagrams such as source inventory, candidate business process flow, or high-level medallion direction when they help review the project. Do not fully design every layer upfront; run focused discovery again before sources, bronze, silver, gold, semantic, evaluator, and documentation phases.

Use Mermaid for every diagram. For entity relationships, use Mermaid `erDiagram`. Verify every Mermaid diagram you add or change is visible/parseable, and record the result in the phase report.

Use full wording in all user-facing plans, reports, summaries, diagram notes, and final handoffs. Avoid shorthand such as primary key abbreviations, foreign key abbreviations, entity relationship diagram abbreviations, documentation abbreviations, repository abbreviations, and continuous integration abbreviations unless quoting a command, filename, package name, environment variable, or official tool name.

After I answer at the discovery checkpoint, run project setup and configuration automatically: write/update `AGENT_PLAN.md` with the setup phase marked as automatic setup-only, create the local dbt scaffold if needed, install missing dependencies, run `dbt debug`, run `dbt deps`, run `dbt parse`, and write the setup report. Interpret my response by the active workflow checkpoint, not by general intent. Discovery checkpoint approval only confirms the source and automatic setup. It does not approve source YAML generation, bronze/staging, silver/intermediate, gold/marts, semantic layer, evaluator, documentation, presentation layer, continuous integration, Agents Schema, commits, pushes, or source switching. Stop and ask first if required settings are missing, the selected profile is unsafe or failing, existing project files would be overwritten, warehouse objects would be created or replaced, credentials are needed, or I explicitly disabled automatic setup.

During project setup and configuration, perform profile target schema hygiene and write the result into `reports/agent/setup_report.md` and `reports/agent/PIPELINE_STATUS.md`: active profile, adapter, database, target schema, source schema, whether the target schema is safe, and any required mitigation. Treat unsafe target schema routing as a setup blocker, not an optional follow-up.

After every bronze/staging, silver/intermediate, and gold/marts build, run warehouse data validation queries before moving to the next layer. Verify row counts, expected-empty evidence, grain, keys, relationships, row-count movement, date coverage, status/category distributions, important measures, mapping coverage, and privacy exposure. Write `Data Verification Results` into the layer report, share the important results with me, and stop when a model expected to contain data is empty or any validation issue is unexplained.

For gold/marts, semantic layer, presentation layer, and final delivery, define key performance indicators with business meaning, source model, grain, numerator, denominator, filters, time field, dimensions, caveats, validation evidence, and approval status. Defer or ask for approval when definitions are ambiguous; do not silently implement advanced metrics.

After marts, semantic layer, evaluator, and documentation are complete, ask whether I want a presentation layer before closing final delivery. Recommend the best option with evidence and list possible key performance indicators, semantic metrics, report or dashboard pages, source models, caveats, and privacy notes. If I approve the presentation layer and do not specify another technology, default to a Power BI PBIP/TMDL project. Create a separate `presentation_layer` phase plan, build the approved artifact, validate it, and write `reports/agent/presentation_report.md`. Do not create dashboards, reports, slides, notebooks, or business intelligence artifacts unless I approve that follow-up work.

The presentation-layer recommendation and my decision are required for full pipeline final delivery. If I have not answered the presentation question, set status to `Documentation complete - presentation decision pending`, not `Delivery complete`. If you cannot produce the recommendation, mark it blocked or skipped with the reason in the final report, pipeline status, context tree, and final response.

Before final delivery, perform an advanced data-engineering review covering source lock, schema hygiene, layer validation, grain, tests, data quality, privacy, key performance indicators, semantic layer, evaluator, documentation, presentation-layer recommendation, and operations.

Before each non-setup build phase, write/update `AGENT_PLAN.md`, explain in Markdown what you will build, and wait for my approval before implementing that phase. Treat each approval as checkpoint-scoped only; after a phase completes, write the phase report, share validation results, and stop at the next phase plan unless I explicitly approved that next named phase too.

In each discovery summary and phase plan, recommend the best next path with evidence, show what looks right, what is not ready yet, confidence about proven vs uncertain items, and what needs my approval. Do not ask me to design everything from scratch.

When sensitive fields or unclear coded fields appear, propose the safe default instead of only asking me what to do. For direct identifiers such as patient names or medical record numbers, recommend excluding, masking, or hashing them from gold/marts by default. For ambiguous, placeholder, abbreviated, generic, or poorly named fields, recommend passing them through bronze/staging as raw unmapped source fields, deferring mapping seeds until definitions are provided, and excluding them from gold/marts unless I approve raw audit exposure. Do not rename unclear fields unless I provide definitions or explicitly ask for suggested names; if I ask for suggestions, analyze values, propose candidate names with confidence, and wait for my approval of the exact final names before changing SQL or YAML.

In each phase plan, include a Data Engineer Decision Check covering grain, keys, joins, bridge tables, mappings, metrics, privacy, materialization, tests, and validation evidence. Ask me before guessing any decision that affects business meaning, privacy, correctness, cost, or downstream usability.

If you cannot properly understand source tables, relationships, business processes, required metrics, data quality rules, required output models, or reporting needs, do not assume. Ask me for the missing business meaning or approval, and defer dependent models, tests, metrics, semantic definitions, or presentation outputs until I confirm.

After each completed or blocked checkpoint, write/update `reports/agent/<phase>_report.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md` with what was done, what passed, warnings/failures/skips, assumptions, user decisions, phase outputs, report links, and open decisions. Also share a short chat result summary with current checkpoint, status, report path, goal, what was completed, what was built or changed, validation, included scope, not-included scope, open decisions, next checkpoint, next goal, next includes, next does not include, and exact approval needed.

Ask me only when required `.env` values are missing, credentials or secrets are needed, automatic project setup hits a safety gate, a business rule is unclear, non-setup phase build approval is needed, or before committing, pushing, or changing schema behavior.
```

## Optional Project Rules

Add this only when the project has business-specific rules, mappings, joins, or privacy requirements.

```text
Project rules:
- Field mappings:
  - <source_table.source_column> -> <target_column>: <meaning/rule>
- Joins:
  - <left_table.column> -> <right_table.column>: <relationship>
- Metrics:
  - <metric_name>: <definition, grain, filters>
- Exclusions:
  - <tables/columns/records to ignore>
- Privacy:
  - <personally identifiable information / protected health information handling, masking, or exclusion rules>
- Naming:
  - <custom naming conventions>
- Special instructions:
  - <anything else the agent must follow>
```

If a rule is unclear, the agent should ask before modeling it.

## Single Phase

Use this only when you want one part of the workflow:

```text
Use the dbt Analytics Engineer skill (`agentic-dbt-pipeline`).

Use settings from `.env`.
workflow_phase: <init | sources | staging | intermediate | marts | semantic_layer | project_evaluator | docs | presentation_layer | ci | agents_schema>

Use `docs` and `ci` only as exact workflow phase values. In explanations, write `documentation` and `continuous integration`.

Before building this phase, explain the plan in Markdown with your recommendation, evidence, confidence, risks, and approval needs, then wait for my approval. After it completes, write/update the phase report, pipeline status, and context tree files.
```
