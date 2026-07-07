# Skill Knowledge Layer

Use this to separate built-in reusable analytics engineering knowledge from project-specific knowledge.

## Purpose

The skill should carry reusable professional knowledge so every new project starts with strong defaults, even when the project has no local knowledge files yet.

Project knowledge files can override or extend this knowledge for a specific domain, client, warehouse, or team.

## Knowledge precedence

Apply knowledge in this order:

1. Current user prompt and explicit approvals
2. Current source data evidence
3. Project knowledge files and `project_rules`
4. Built-in skill knowledge references
5. General model knowledge

If built-in skill knowledge conflicts with source evidence or user rules, stop and ask before applying it.

## Built-in reusable knowledge references

Read these skill references as needed:

| Knowledge area | Skill reference |
|---|---|
| dbt architecture, testing, documentation, incremental models, snapshots, packages, semantic layer, and build process | [data-engineering-best-practices.md](data-engineering-best-practices.md), [principal-data-engineering-standards.md](principal-data-engineering-standards.md), phase-specific files |
| dbt packages and agent skills | [dbt-packages-and-skills.md](dbt-packages-and-skills.md) |
| Materialization and performance defaults | [materialization-rules.md](materialization-rules.md), [principal-data-engineering-standards.md](principal-data-engineering-standards.md) |
| Big data, modern table formats, partitioning, clustering, compaction, and warehouse optimization | [principal-data-engineering-standards.md](principal-data-engineering-standards.md) |
| Evidence-driven build, data quality, and per-layer validation | [evidence-driven-dbt-process.md](evidence-driven-dbt-process.md), [layer-data-validation.md](layer-data-validation.md), [layer-verification-ledger.md](layer-verification-ledger.md), [data-engineering-best-practices.md](data-engineering-best-practices.md) |
| Universal analytics and dashboard coverage | [universal-analytics-framework.md](universal-analytics-framework.md), [analytics-insight-reporting.md](analytics-insight-reporting.md), [reporting-standards.md](reporting-standards.md) |
| Key performance indicators and semantic metrics | [kpi-definitions.md](kpi-definitions.md), [kpi-definition-contract.md](kpi-definition-contract.md), [metric-verification.md](metric-verification.md), [metric-verification-checklist.md](metric-verification-checklist.md), [semantic-layer-spec.md](semantic-layer-spec.md) |
| Matplotlib presentation layer | [matplotlib-presentation-layer.md](matplotlib-presentation-layer.md), [presentation-layer.md](presentation-layer.md), [universal-analytics-framework.md](universal-analytics-framework.md), [analytics-insight-reporting.md](analytics-insight-reporting.md), [reporting-standards.md](reporting-standards.md) |
| Power BI and presentation layer design | [presentation-layer.md](presentation-layer.md), [universal-analytics-framework.md](universal-analytics-framework.md), [analytics-insight-reporting.md](analytics-insight-reporting.md), [principal-data-engineering-standards.md](principal-data-engineering-standards.md) |
| Privacy, sensitive fields, and unclear fields | [privacy-and-unknown-fields.md](privacy-and-unknown-fields.md) |
| Source safety and warehouse routing | [source-confirmation.md](source-confirmation.md), [warehouse-adapter-routing.md](warehouse-adapter-routing.md), [schema-isolation.md](schema-isolation.md) |

## External documentation

Use official documentation when the task depends on current behavior, adapter-specific syntax, package versions, or platform features. Prefer primary sources:

- dbt official documentation for dbt Core, model config, tests, snapshots, semantic layer, and commands
- Package documentation or package source repositories for dbt packages
- Warehouse documentation for PostgreSQL, Redshift, Snowflake, BigQuery, Databricks, Spark, Iceberg, Delta Lake, or Hudi behavior
- Microsoft documentation for Power BI, PBIP, TMDL, and Tabular model behavior
- Matplotlib official documentation for figures, axes, artists, colors, text, and static report rendering at https://matplotlib.org/stable/users/index

Do not paste large external documentation into the project. Summarize the relevant rule in the phase plan or report, cite the source when browsing was used, and keep implementation grounded in the current project.

## How to use this knowledge

- Use built-in knowledge to recommend the professional default.
- Do not use built-in knowledge to invent business meaning.
- Do not force every advanced feature into every project.
- Mark advanced items as `applied`, `deferred`, `not applicable`, or `needs approval`.
- Ask the user when the knowledge affects business meaning, privacy, cost, production behavior, or downstream presentation.

## When project knowledge should be added

Ask whether to persist knowledge when the user provides reusable local rules such as:

- Domain definitions and business process rules
- Metric definitions and accepted filters
- Field mappings and code meanings
- Privacy and masking policy
- Team naming conventions
- Warehouse-specific performance patterns
- Analytics insight reporting standards
- Accepted evaluator exceptions

Store project-specific knowledge in the project files listed in [project-knowledge.md](project-knowledge.md), not in this skill reference.
