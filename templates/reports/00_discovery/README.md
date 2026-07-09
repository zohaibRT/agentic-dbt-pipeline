# Discovery Folder Guide

Read this file first when opening `reports/agent/00_discovery/`.

Status meanings: see [references/discovery-status-vocabulary.md](../../../references/discovery-status-vocabulary.md) in the skill repo, or the **Status Vocabulary** section below.

## Files in this folder

| File | What it is | Why it exists | Updated when |
|---|---|---|---|
| `README.md` | This guide | Helps humans understand discovery outputs | When discovery process changes |
| `core_profile.json` | Connection context snapshot (no secrets) | Reload project context without chat | **Every discovery run** |
| `discovery_raw.json` | Structured warehouse evidence | Audit trail before human summaries | **Every discovery run** |
| `discovery_report.md` | Main discovery summary | Human-readable findings | **Every discovery run** |
| `requirements.md` | Requirements from source evidence | Bridge to build planning | **Every discovery run** |
| `cardinality_report.md` | Join safety and row multiplication risks | Prevent unsafe joins | When relationships exist |
| `relationship_profile.md` | Proven and uncertain relationships | ER/join planning | When relationships exist |
| `DISCOVERY_APPROVAL_CHECKLIST.md` | Approval gate before build | Stop unsafe continuation | **Every discovery run** |
| `sql_proofs/` | Runnable SQL proof files | Evidence you can re-run | **Every discovery run** |

## Status vocabulary

| Status | Meaning | Why you might see it |
|---|---|---|
| **PASS** | Check succeeded; claim is supported | Counts, keys, or relationships look correct |
| **WARN** | Usable with a documented limitation | Empty table, accepted orphan rate, inferred meaning not yet approved |
| **FAIL** | Claim is wrong or unsafe | Duplicate grain, wrong schema, broken proof |
| **BLOCKED** | Waiting on user decision or missing input | Unapproved source switch, unclear business rule |
| **SKIPPED** | Check not run on purpose | Not applicable or excluded from v1 scope |

`WARN` is not failure. It means: **we can continue, but read the note.**

## JSON files

### `core_profile.json`

Open `_file_meta` first. This file stores:

- dbt profile name
- adapter
- database or catalog
- source schema
- domain and project paths

It must **never** contain passwords or tokens.

### `discovery_raw.json`

Open `_file_meta` first. This file stores structured discovery output:

- run metadata
- scope counts (total / included / deferred / excluded tables)
- `tables[]` with row counts and optional column, key, relationship, and sample detail
- `queries_executed[]` linking back to `sql_proofs/`

For large schemas, every table should appear with at least `table_name` and `row_count`. Deep column and sample detail is required only for included or priority tables.

## SQL proofs

See `sql_proofs/_proof_index.md` for the proof map.

Number bands:

| Band | Proof type |
|---|---|
| 001 | Full table inventory |
| 010+ | Row counts for priority or included tables |
| 020+ | Key / grain checks |
| 030+ | Status distributions |
| 060+ | Relationship checks |
| 080+ | Compare / quality checks |

For thousands of tables, use `001` for all counts; do not create thousands of `010+` files.
