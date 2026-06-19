# Human Review Checkpoint

The agent should build the first working version. The engineer or domain owner should review and approve the business meaning.

## Review after each layer

After staging:

- Source tables represented correctly
- Column renames and casts are safe
- Primary key and relationship assumptions are reasonable
- Tests match the data, not guesses

After intermediate:

- Joins preserve the intended grain
- Business rules are applied in the correct layer
- Mapping seeds or reference tables are used correctly
- Duplicates and nulls are handled intentionally

After marts:

- Facts and dimensions match the target reporting grain
- Metrics are understandable and reproducible
- Raw/private fields are hidden when not needed
- Models are ready for BI or semantic layer use

After docs/evaluator:

- Important warnings are reviewed
- Model and column descriptions explain grain and business logic
- Known limitations are documented

## Ask for approval when

- A model changes business meaning
- A join can multiply rows
- A metric definition is ambiguous
- Mapping values are incomplete
- Private, sensitive, PII, or PHI fields may reach marts
- Performance changes require tables or incremental models

## Summary format

Use this review summary:

```text
Layer reviewed:
What changed:
Business assumptions:
Data quality notes:
Tests/build result:
Open decisions:
Approval needed:
```
