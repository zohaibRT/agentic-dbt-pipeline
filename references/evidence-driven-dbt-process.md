# Evidence-Driven dbt Build Process

Use this before any phase can be marked complete.

## Core rule

The agent is allowed to build only what it can prove.

`dbt build` proves that the project can run. It does not prove that the business logic, data grain, key performance indicators, measures, metrics, or dashboard values are correct.

No model, metric, key performance indicator, measure, dashboard value, or phase can be marked complete unless it has a corresponding verification record.

## Correctness levels

| Level | Meaning | Required evidence |
|---|---|---|
| Technical correctness | SQL runs and dbt artifacts compile/build | `dbt parse`, `dbt build`, tests, `target/run_results.json` |
| Data correctness | Rows, grain, relationships, joins, dates, statuses, and amounts behave as expected | SQL proof files, row-count movement, duplicate checks, orphan checks, join multiplication checks |
| Business correctness | The definition matches what the business means | Requirement contract, key performance indicator contract, approval status, source mapping, expected-versus-actual reconciliation |

Technical correctness is required but never sufficient by itself.

## Required workflow

```text
Business truth
-> data discovery proof
-> requirement contract
-> model build
-> model verification
-> key performance indicator contract
-> key performance indicator reconciliation
-> independent verification
-> human sign-off
```

Do not use this unsafe shortcut:

```text
Discovery
-> build dbt models
-> generate dashboard
-> assume the numbers are correct
```

## Required verification record

Every important output must answer:

| Question | Evidence |
|---|---|
| What was required? | Requirement row in `reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md` |
| Where was it built? | dbt model, semantic metric, presentation measure, or report artifact path |
| How was it tested? | dbt test, warehouse query, source-to-mart reconciliation, presentation validation |
| What was the result? | Captured result, expected result, difference or tolerance, status |
| Who approved the meaning? | Approval status, user decision, or blocked/deferred note |

Each verification record must include:

```text
Business definition
Source mapping
dbt model location
SQL proof file
Captured result
Expected result
Difference or tolerance
PASS / WARN / FAIL / BLOCKED status
Explanation of why the result is correct
```

## Required generated reports

Generated dbt projects must maintain these cross-phase verification files:

```text
reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md
reports/agent/LAYER_VERIFICATION_LEDGER.md
reports/agent/KPI_DEFINITION_CONTRACTS.md
reports/agent/METRIC_VERIFICATION_MATRIX.md
reports/agent/INDEPENDENT_VERIFICATION_REPORT.md
```

Phase-specific SQL proofs still live in the managed phase folders from [report-artifact-organization.md](report-artifact-organization.md).

## Completion rule

Do not claim a phase is complete when:

- A requirement has no implementation artifact or documented exclusion.
- A model has no row count, grain, key, or relationship evidence when applicable.
- A key performance indicator lacks a contract.
- A metric or measure lacks source-to-final reconciliation.
- A presentation value cannot be traced back to a verified model, semantic metric, or SQL proof.
- The acceptance gate or independent verifier returns `FAIL`.

Use `WARN` only when the limitation is documented, non-critical, and safe for human review.
