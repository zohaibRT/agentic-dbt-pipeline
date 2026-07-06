# Requirements Traceability Matrix

Use this file to keep discovery requirements aligned with sources, bronze/staging, silver/intermediate, gold/marts, semantic, analytics, and presentation layers.

Canonical location in generated projects:

```text
reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md
```

## Core rule

Every approved requirement from `reports/agent/00_discovery/requirements.md`, user `project_rules`, and later approved scope changes must have an owner, implementation target, validation proof, and status.

A requirement is not complete just because a model exists. It is complete only when the related model, test, SQL proof, phase report, and user-facing/reporting output are linked.

## Required table

```markdown
# Requirements Traceability Matrix

| Requirement ID | Requirement / Rule | Source | Business Area | Layer Impact | Implementation Artifact | Verification Artifact | Presentation / Output Artifact | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| REQ-001 | <approved requirement> | requirements.md / project_rules / user | <area> | sources/bronze/silver/gold/semantic/presentation | <model/seed/yaml/metric/report path> | <sql_proof path + phase report section> | <dashboard/report/docs path or N/A> | OPEN / IN_PROGRESS / PASS / WARN / FAIL / BLOCKED / DEFERRED | <evidence or decision> |
```

## Required behavior

Update this matrix:

1. After discovery creates `requirements.md`.
2. When the user adds or changes `project_rules`.
3. Before each non-setup phase plan is approved.
4. After each phase completes.
5. Before analytics insight reporting.
6. Before presentation work.
7. Before final delivery.

## Status rules

| Status | Meaning |
|---|---|
| OPEN | Requirement exists but implementation is not planned yet. |
| IN_PROGRESS | Requirement is included in the active or approved phase plan. |
| PASS | Requirement was implemented and verified with proof. |
| WARN | Requirement is partially implemented or depends on known data limitation. |
| FAIL | Requirement was implemented but validation failed. |
| BLOCKED | Requirement cannot be completed until a missing input, source, credential, or business decision is resolved. |
| DEFERRED | User or agent intentionally postponed it with evidence. |

## Hard gate

Final delivery must not be marked `PASS` when any non-deferred requirement is `OPEN`, `IN_PROGRESS`, `FAIL`, or `BLOCKED`.
