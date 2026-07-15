# Human Review Checkpoint

The agent must explain and get approval for the plan before each phase. After the build, the engineer or domain owner should review and approve the business meaning.

Pre-build plan approval: [phase-plan-approval.md](phase-plan-approval.md).

## Review after each layer

After every layer, also open:

- `reports/agent/HUMAN_ATTENTION_BOARD.md` — what you must answer now
- `reports/agent/KPI_GAP_REGISTER.md` — KPIs we can make after those gaps are fixed

The chat summary must re-warn OPEN gaps every checkpoint. Do not assume a prior approval meant those KPIs were unlocked.

After staging:

- Source tables represented correctly
- Column renames and casts are safe
- Primary key and relationship assumptions are reasonable
- Tests match the data, not guesses
- Gap Register still lists blocked makeable KPIs when known

After intermediate:

- Joins preserve the intended grain
- Business rules are applied in the correct layer
- Mapping seeds or reference tables are used correctly
- Duplicates and nulls are handled intentionally
- Unmapped statuses/dates still block lifecycle KPIs until you define them

After marts:

- Facts and dimensions match the target reporting grain
- Metrics are understandable and reproducible
- Raw/private fields are hidden when not needed
- Models are ready for BI or semantic layer use
- Missing dims / money units / Active-Delivered definitions still appear as OPEN KPI gaps

After docs/evaluator:

- Important warnings are reviewed
- Model and column descriptions explain grain and business logic
- Known limitations are documented
- Gap Register and Attention Board still list unresolved KPI blockers
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
Open decisions: (IDs from reports/agent/HUMAN_ATTENTION_BOARD.md only)
Approval needed:
```

Do not repeat full inventories or cardinality matrices in the human review summary. Put OPEN decisions only on the Attention Board per [human-attention-reporting.md](human-attention-reporting.md).