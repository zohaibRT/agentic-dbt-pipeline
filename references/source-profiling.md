# Source Profiling Checklist

Run lightweight project discovery before any build planning with [discovery-requirements.md](discovery-requirements.md). Then use [phased-discovery.md](phased-discovery.md) to profile only what is needed for the current phase. Run this deeper source profiling after source YAML is generated and before staging models are designed.

## Goal

Understand the real source data before modeling. Do not infer business meaning from table names alone.

## Inspect

For each source table, capture:

- Row count
- Candidate primary key columns
- Candidate foreign key columns
- Date and timestamp columns
- Amount, quantity, score, duration, or other numeric measure columns
- Status, type, category, flag, and code columns
- Nullable columns that look important
- Duplicate keys
- Empty tables

Use warehouse SQL, dbt source metadata, or codegen output through the adapter selected by the active dbt profile. Follow [warehouse-adapter-routing.md](warehouse-adapter-routing.md) before profiling. Keep queries lightweight and avoid full table scans when tables are large.

Do not use another warehouse connector as a profiling fallback. If the selected profile is PostgreSQL, profile PostgreSQL only. If the selected profile is Redshift, profile Redshift only. If the selected profile fails, stop and ask whether to fix the profile or switch profiles.

## Record findings

Add short notes to source YAML descriptions or a project note when helpful:

- Table grain
- Primary key assumption
- Known relationships
- Important date column
- Important status/code values
- Data quality concerns
- Empty or low-row-count tables

When relationship findings are diagrammed, use Mermaid `erDiagram` per [mermaid-diagrams.md](mermaid-diagrams.md). Only draw relationships that are supported by profiling, constraints, source metadata, or user-approved rules. Record uncertain relationships as notes outside the diagram.

## Stop and ask

Ask the user before modeling if:

- No stable primary key can be found for an important table
- A required table is empty
- A relationship is unclear
- Multiple date columns could drive the same fact
- Important columns have ambiguous names
- The prompt includes business rules that conflict with the data

## Validate

At minimum, run source-level checks or SQL inspections for:

- Row counts
- Duplicate primary keys
- Null primary keys
- Distinct values for important status/code columns
- Min/max dates for important date columns

Use these findings to choose staging tests and intermediate joins.
