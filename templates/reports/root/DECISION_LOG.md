# Decision Log

Append-only human decision history. Do **not** overwrite prior decisions. Maintain version history by adding new rows and linking `Previous Decision Reference`.

| Decision ID | Original Question | Options Considered | Machine Recommendation | Final Human Decision | Decision Owner | Approver | Date | Evidence | Affected Models | Affected Metrics | Revalidation Requirement | Previous Decision Reference | Decision Type |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DL-001 | <question> | <options> | <machine recommendation> | <human decision> | <owner> | <approver> | YYYY-MM-DD | `<path>` | <models> | <metrics> | <when to revalidate> | none | MACHINE_RESOLVABLE / HUMAN_DECISION_REQUIRED / HYBRID_DECISION |

## Classification

- MACHINE_RESOLVABLE — agent should resolve with evidence (counts, null rates, SQL, numeric reconciliation)
- HUMAN_DECISION_REQUIRED — agent must not guess (definitions, ownership, targets, status meanings)
- HYBRID_DECISION — preserve both machine_recommendation and final human decision
