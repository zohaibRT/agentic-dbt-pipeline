# Layer Verification Ledger

Use this file to prove that every dbt layer was verified with runnable evidence, not only a successful `dbt build`.

Canonical location in generated projects:

```text
reports/agent/LAYER_VERIFICATION_LEDGER.md
```

## Core rule

Every created or changed model in sources, bronze/staging, silver/intermediate, gold/marts, semantic, analytics, and presentation scope must have a verification row.

## Required table

```markdown
# Layer Verification Ledger

| Phase | Layer | Model / Artifact | Expected Grain | Row Count | Upstream Comparison | Key / Grain Proof | Relationship Proof | Measure / KPI Proof | Privacy Check | Proof Files | dbt Command Result | Overall Status | Notes |
|---|---|---|---|---:|---|---|---|---|---|---|---|---|---|
| 03_bronze | bronze/staging | stg_source__table | <grain> | <count> | <source count comparison> | PASS/WARN/FAIL/SKIPPED | PASS/WARN/FAIL/SKIPPED | PASS/WARN/FAIL/SKIPPED | PASS/WARN/FAIL/SKIPPED | reports/agent/03_bronze/sql_proofs/... | PASS/WARN/FAIL/BLOCKED | PASS/WARN/FAIL/BLOCKED | <notes> |
```

## Required proof coverage by layer

| Layer | Minimum proof coverage |
|---|---|
| Discovery | source inventory, row counts, key candidates, status distributions, date coverage, numeric summaries, relationship candidates |
| Sources | source YAML existence, source table availability, source freshness where possible, source tests where generated |
| Bronze / staging | source-to-staging row counts, grain/key checks, accepted values, date coverage, raw numeric summaries, privacy pass-through decisions |
| Silver / intermediate | row presence, join safety, row loss/multiplication, mapping coverage, relationship integrity, derived measure/flag sanity |
| Gold / marts | fact/dimension row counts, grain uniqueness, relationship integrity, bridge table checks, privacy exposure, KPI component checks |
| Semantic | semantic metric definitions tied to approved gold/KPI proofs, semantic metric SQL comparison |
| Analytics insight reporting | catalogs, KPI discovery matrix, KPI proof references, reconciliation, variance, backlog |
| Presentation | figure/KPI coverage, SQL-backed chart data, smoke test, rendered/deferred/blocked status |

## Hard gate

A phase may not move to the next phase when any model expected to contain data is empty, duplicated at declared grain, has unexplained row multiplication/loss, has broken required relationships, exposes sensitive fields without approval, or has unreconciled KPI logic.
