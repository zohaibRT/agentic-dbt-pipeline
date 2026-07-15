# Human Attention Board

## Purpose

This is the **only** file a human should need for “what do you need from me?”  
Technical detail stays in phase reports and `sql_proofs/`. Do not duplicate full matrices here.

For every OPEN decision, the agent must recommend a concrete answer first. The human accepts, overrides, or defers.

The agent may discover evidence and recommend options. The agent must **not** approve business definitions, targets, inclusion rules, or production release.

## Decision table

| Decision ID | Decision Type | Area | Business Process | Object Type | Object ID | Question Requiring Human Input | Machine Evidence | Machine Recommendation | Alternative Options | Risk of No Decision | Proposed Owner | Due or Review Condition | Status | Final Human Decision | Approval Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| <D-01> | HUMAN_DECISION_REQUIRED | kpi | <process> | kpi | KPI-001 | <question> | `<evidence>` | <recommendation> | <alternatives> | <risk> | <owner> | <due> | OPEN | | |

Allowed statuses: OPEN, PENDING_REVIEW, APPROVED, APPROVED_WITH_CONDITIONS, REJECTED, BLOCKED, DEFERRED.

## Quick Links

| Need | File |
|---|---|
| Business approvals | `BUSINESS_APPROVAL_REGISTER.md` |
| Decision history | `DECISION_LOG.md` |
| KPI contracts | `KPI_DEFINITION_CONTRACTS.md` |
| Verification checklist | `HUMAN_VERIFICATION_GUIDE.md` |
