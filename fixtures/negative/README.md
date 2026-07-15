# Negative fixtures

Invalid cases are **not** committed as full dbt projects.

Use:

```bash
python scripts/run_negative_fixture_suite.py
```

The suite copies a valid DuckDB fixture, applies one intentional defect, and
asserts the targeted validator fails for the documented reason.

Synthetic approval evidence in valid fixtures is labelled:

`TEST FIXTURE — NOT PRODUCTION APPROVAL`

The independent verifier rejects those markers outside `fixtures/` paths.
