# Documentation Report

## Template Use

Use this file as the fixed structure for `reports/agent/08_documentation/docs_report.md`.
Replace placeholders with dbt documentation generation and artifact evidence.

## Summary

- Status: <PASS / WARN / FAIL / BLOCKED>
- Documentation generated: <yes/no>
- Manifest path: `target/manifest.json`
- Catalog path: `target/catalog.json`

## Documentation Coverage

| Area | Status | Evidence | Notes |
|---|---|---|---|
| Source descriptions | <PASS/WARN/FAIL/BLOCKED> | <path/result> | <notes> |
| Model descriptions | <PASS/WARN/FAIL/BLOCKED> | <path/result> | <notes> |
| Column descriptions | <PASS/WARN/FAIL/BLOCKED> | <path/result> | <notes> |
| Tests documented | <PASS/WARN/FAIL/BLOCKED> | <path/result> | <notes> |
| Lineage/DAG generated | <PASS/WARN/FAIL/BLOCKED> | <path/result> | <notes> |

## Validation

| Command / Check | Result | Evidence |
|---|---|---|
| dbt docs generate | <PASS/WARN/FAIL/SKIPPED> | <command/result> |
| dbt parse | <PASS/WARN/FAIL/SKIPPED> | <command/result> |
| Artifact existence | <PASS/WARN/FAIL/BLOCKED> | <paths> |

## Open Decisions

- <decision or "None">

## Next Action

- <recommended next checkpoint and approval needed>
