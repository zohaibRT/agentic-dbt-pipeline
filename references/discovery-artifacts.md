# Discovery Artifacts Guide

Use this to understand every file under `reports/agent/00_discovery/` and the mandatory discovery JSON artifacts.

Also read [discovery-status-vocabulary.md](discovery-status-vocabulary.md) before interpreting any `PASS`, `WARN`, `FAIL`, or `BLOCKED` value.

## Mandatory discovery outputs

Discovery must create or fully update these files every run:

```text
reports/agent/00_discovery/README.md
reports/agent/00_discovery/core_profile.json
reports/agent/00_discovery/discovery_raw.json
reports/agent/00_discovery/discovery_report.md
reports/agent/00_discovery/requirements.md
reports/agent/00_discovery/cardinality_report.md
reports/agent/00_discovery/relationship_profile.md
reports/agent/00_discovery/DISCOVERY_APPROVAL_CHECKLIST.md
reports/agent/00_discovery/sql_proofs/
reports/agent/PIPELINE_STATUS.md
reports/agent/CONTEXT_TREE.md
reports/agent/REPORT_INDEX.md
reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md
reports/agent/NEXT_PHASE_PROMPT.md
```

`core_profile.json` and `discovery_raw.json` are **required**, not optional.

## Machine-readable JSON files

### `core_profile.json`

| Field | Purpose |
|---|---|
| **What** | Non-secret connection and project context snapshot |
| **Why** | Lets a later agent or verifier reload context without chat history |
| **When** | Created at setup from template; **fully updated every discovery run** |
| **Secrets** | Never store passwords, tokens, or private keys |

### `discovery_raw.json`

| Field | Purpose |
|---|---|
| **What** | Structured warehouse evidence before human summaries |
| **Why** | Audit trail of what the database actually returned |
| **When** | **Fully updated every discovery run** |
| **Large schemas** | Inventory all tables with counts; deep column/sample detail only for included or priority tables |

Both JSON files use a top-level `_file_meta` object because JSON cannot contain comments. Read `_file_meta` first.

## Human-readable discovery files

| File | What it answers |
|---|---|
| `README.md` | What each discovery file is for |
| `discovery_report.md` | What did we find in the source? |
| `requirements.md` | What should the project build? |
| `cardinality_report.md` | Are joins safe or do they multiply rows? |
| `relationship_profile.md` | How do tables connect? |
| `DISCOVERY_APPROVAL_CHECKLIST.md` | Is discovery approved before build? |
| `sql_proofs/` | Runnable SQL evidence |

## Large schema rule

If the source schema has hundreds or thousands of tables:

1. Put **all tables** in `001_source_table_inventory.sql` and `discovery_raw.json.tables[]` with at least `table_name` and `row_count`.
2. Apply the table inclusion filter in [table-inclusion-priority-filter.md](table-inclusion-priority-filter.md).
3. Mark each table `included`, `deferred`, or `excluded` with a reason.
4. Create deep per-table proofs only for **included** or **priority** tables.
5. Do not create one row-count proof file per table when the schema is very large.

## Table inclusion and priority filter

Read [table-inclusion-priority-filter.md](table-inclusion-priority-filter.md) before narrowing discovery scope.

Mandatory reusable checklist:

1. Keep fact/event tables on the main process
2. Keep related dimensions/lookups for included facts
3. Exclude audit/log/platform/empty unless the user requested them
4. Require an `inclusion_reason` for every table
5. Ask the user if process scope is unclear

Required outcome:

- `001_source_table_inventory.sql` covers every table
- first-pass business process is named
- every table has `inclusion_status` + `inclusion_reason`
- deep proofs (`010+` and later) cover only included/priority tables
- `discovery_report.md` includes a **Table Inclusion Filter** section with the checklist above

## Templates

Canonical templates live under:

```text
templates/reports/00_discovery/
```

The agent must start from these templates and replace placeholder content with source evidence.
