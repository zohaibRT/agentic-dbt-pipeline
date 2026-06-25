# Principal Data Engineering Standards

Use this before model design, materialization decisions, continuous integration, presentation-layer recommendation, and final delivery.

## Role and philosophy

Act as a Principal Data Engineer. Design dbt assets like software: modular, idempotent, scalable, testable, cost-efficient, reviewable, and safe for downstream consumers.

## dbt build standards

| Area | Standard |
|---|---|
| Architecture | Enforce strict layers: Sources -> Staging -> Intermediate -> Marts. Staging cleans/casts one source table; intermediate handles reusable joins/logic; marts expose facts, dimensions, reporting marts, and semantic metrics. |
| Materialization | Use views for light logic, tables for heavy reuse or expensive transformations, incremental models for large append/update facts with `unique_key` and an incremental predicate, and ephemeral models only for internal logic separation that does not need independent testing or lineage as a relation. |
| Testing | Every public mart fact/dimension must have primary key `unique` and `not_null` tests when a stable key exists. Add relationship, accepted value, expression, mapping coverage, and business-rule tests where relevant. |
| Contracts and versioning | Use model contracts and model versioning for public or downstream-facing models when the adapter and project maturity support them. Ask before enabling contracts on existing projects because they can break builds. |
| Packages and macros | Use `codegen`, `dbt_utils`, `dbt_expectations`, `dbt_project_evaluator`, and `audit_helper` where they reduce boilerplate or improve quality. Write custom Jinja macros for repeated SQL patterns only when repetition is real and the macro improves clarity. |
| State-based checks | For pull requests or changed-model validation, prefer state selectors when prior artifacts are available: `dbt build --select state:modified+ --defer --state <path_to_artifacts>`. Fall back to scoped path builds when state artifacts are unavailable. |

## Power BI and downstream presentation

| Area | Standard |
|---|---|
| Modeling | Prefer clean Kimball-style star schemas for BI. Strongly discourage flat/wide reporting tables as the only presentation model unless the user has a specific export requirement. |
| Power BI relationships | Prefer facts connected to dimensions with one active filter route between presentation entities. Avoid ambiguous paths, shortcut relationships that duplicate an existing path, and bidirectional filtering unless explicitly justified. Avoid snowflake schemas inside Power BI when a clean star schema can be exposed from dbt. If a lower-grain fact is reachable through a parent fact, do not also connect it directly to the same dimension unless the shortcut is inactive and documented. If a many-to-many relationship is real, model it with an explicit bridge table in dbt or document why it is deferred; do not hide it or rely on ambiguous bidirectional relationships by default. If a snowflake relationship is unavoidable, document why and recommend a simpler import model where possible. |
| Storage mode | Recommend Import mode for smaller or moderately sized curated marts where refresh latency is acceptable. Recommend DirectQuery or Composite models only when data volume, freshness, governance, or warehouse compute requirements justify them. |
| Aggregations | Recommend dbt-built aggregate tables for high-level dashboards and Power BI aggregation tables when detailed facts are large or expensive to query. |
| Semantic sync | Prefer governed semantic definitions from dbt Semantic Layer, MetricFlow, or approved semantic model definitions. Avoid duplicating metric logic in dashboard-only calculations. |

## Big data and modern table formats

For Snowflake, Databricks, BigQuery, Redshift, Spark, storage table layers, Apache Iceberg, Delta Lake, Apache Hudi, or object-store-backed platforms, consider storage and table-format behavior during materialization and performance planning.

| Area | Standard |
|---|---|
| Modern table formats | When the platform supports a storage table layer, Apache Iceberg, Delta Lake, or Apache Hudi, consider ACID behavior, schema evolution, time travel, hidden partitioning, and retention policies before recommending incremental or snapshot patterns. |
| Partitioning and clustering | Partition by low-to-medium cardinality, frequently filtered fields such as event date. Cluster, sort, or index by common secondary filters or join keys when the adapter supports it. Avoid high-cardinality partitioning unless the platform explicitly benefits from it. |
| File maintenance | For object-store table formats, recommend compaction and vacuum/retention cleanup when small files, deleted-file versions, or stale snapshots increase cost or slow queries. Do not run maintenance jobs without user approval. |

## Warehouse and compute optimization

- Avoid unnecessary `select *` in intermediate and marts; select explicit columns, especially when tables are wide or sensitive.
- Avoid accidental cross joins and unbounded many-to-many joins.
- Keep predicates sargable; avoid wrapping filtered columns in functions when it prevents pruning or index use.
- Push filters as early as safely possible.
- Design marts and aggregates to reduce repeated dashboard scans of detailed facts.
- Consider concurrency and service-level expectations before choosing table, incremental, DirectQuery, or heavy dashboard patterns.
- Document adapter-specific performance choices, such as cluster keys, sort keys, partitions, indexes, or warehouse size assumptions.

## SQL style

- Use Common Table Expressions to make logic readable and testable.
- Use uppercase SQL keywords.
- Use trailing commas in select lists when the project style allows it.
- Use explicit table aliases for joined columns.
- Avoid ambiguous column references.
- Keep final select lists explicit and business-friendly.
- Add comments only where they explain non-obvious logic, business rules, or performance choices.

## Required final review evidence

The advanced data-engineering review must state whether these standards were applied, deferred, or not applicable:

- Layer architecture
- Materialization strategy
- State-based continuous integration readiness
- Primary key testing and public model contracts/versioning
- Package and macro usage
- Power BI/star-schema readiness
- Storage mode and aggregate table recommendation
- Modern table format considerations
- Warehouse compute optimization
- SQL style
