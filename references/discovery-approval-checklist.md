# Discovery Approval Checklist

Use this checklist after the discovery phase and before starting bootstrap, staging, bronze, silver, gold, semantic, analytics, or presentation work.

The completed checklist must be saved in the generated project as:

```text
reports/agent/00_discovery/DISCOVERY_APPROVAL_CHECKLIST.md
```

The agent must not continue to bootstrap/build unless the final decision is `APPROVED` or `APPROVED WITH CONDITIONS`.

## Status Values

Use only:

- `PASS`
- `WARN`
- `FAIL`
- `BLOCKED`
- `N/A`

## 1. Required Discovery Outputs

| Check | Status | Evidence / Notes |
|---|---|---|
| `reports/agent/00_discovery/discovery_report.md` exists | TODO | |
| `reports/agent/00_discovery/requirements.md` exists | TODO | |
| `reports/agent/00_discovery/cardinality_report.md` exists | TODO | |
| `reports/agent/00_discovery/relationship_profile.md` exists | TODO | |
| `reports/agent/00_discovery/sql_proofs/` exists | TODO | |
| `reports/agent/PIPELINE_STATUS.md` updated | TODO | |
| `reports/agent/CONTEXT_TREE.md` updated | TODO | |
| `AGENT_PLAN.md` created or updated | TODO | |

Decision rule: FAIL if any required file is missing.

## 2. Environment and Source Scope

| Check | Status | Evidence / Notes |
|---|---|---|
| Correct dbt profile identified | TODO | |
| Correct adapter identified | TODO | |
| Correct database inspected | TODO | |
| Correct source schema inspected | TODO | |
| Source tables were discovered, not guessed | TODO | |
| Excluded tables are listed with reasons | TODO | |
| Empty tables are listed with reasons | TODO | |

Decision rule: FAIL if the wrong database/schema/profile was used.

## 3. Source Table Inventory

| Check | Status | Evidence / Notes |
|---|---|---|
| All expected source tables are listed | TODO | |
| Row counts captured for important tables | TODO | |
| Important columns identified | TODO | |
| Important date columns identified | TODO | |
| Important measure columns identified | TODO | |
| Important status/category columns identified | TODO | |
| Unused or low-value tables identified | TODO | |

Decision rule: FAIL if important source tables are missing or row counts are not captured.

## 4. Grain and Key Checks

| Check | Status | Evidence / Notes |
|---|---|---|
| Grain identified for each important table | TODO | |
| Primary/candidate keys identified | TODO | |
| Duplicate key checks completed | TODO | |
| Null key checks completed | TODO | |
| Composite key requirements identified, if needed | TODO | |
| Tables without reliable keys are flagged | TODO | |

Decision rule: FAIL if grain is missing for important tables.

## 5. Relationship and Cardinality Checks

| Check | Status | Evidence / Notes |
|---|---|---|
| Main parent-child relationships identified | TODO | |
| Cardinality checked for important joins | TODO | |
| Orphan checks completed | TODO | |
| Many-to-many risks identified | TODO | |
| Bridge tables identified, if any | TODO | |
| Unsafe joins are marked as risks | TODO | |
| Join paths for future marts are recommended | TODO | |

Decision rule: FAIL if unsafe joins are recommended without warning.

## 6. Data Quality Checks

| Check | Status | Evidence / Notes |
|---|---|---|
| Row count checks completed | TODO | |
| Null checks completed for important fields | TODO | |
| Duplicate checks completed for keys | TODO | |
| Date range checks completed | TODO | |
| Status/category distributions checked | TODO | |
| Amount/quantity sanity checks completed | TODO | |
| Negative or unusual measure values identified | TODO | |
| Unexpected future/past dates identified | TODO | |
| Data quality risks documented | TODO | |

Decision rule: WARN if issues exist but are documented. FAIL if major quality risks are ignored.

## 7. Business Process Understanding

| Check | Status | Evidence / Notes |
|---|---|---|
| Main business process described | TODO | |
| Business process matches source data | TODO | |
| Candidate facts identified | TODO | |
| Candidate dimensions identified | TODO | |
| Important lifecycle/status flow understood | TODO | |
| Business assumptions listed | TODO | |
| Unclear business meanings listed as questions | TODO | |

Decision rule: FAIL if the wrong business process is inferred.

## 8. Privacy and Sensitive Data

| Check | Status | Evidence / Notes |
|---|---|---|
| Sensitive columns identified | TODO | |
| PII fields identified | TODO | |
| Financial/medical sensitive fields identified, if applicable | TODO | |
| Fields to exclude from gold/presentation are listed | TODO | |
| Masking/hashing recommendations documented | TODO | |
| Privacy risks documented | TODO | |

Decision rule: FAIL if obvious sensitive fields are ignored.

## 9. Candidate Metrics and KPI Direction

| Check | Status | Evidence / Notes |
|---|---|---|
| Candidate metrics listed | TODO | |
| Metrics marked as draft unless approved | TODO | |
| Numerator/denominator logic defined where possible | TODO | |
| Date basis identified | TODO | |
| Status filters identified | TODO | |
| Currency handling identified, if applicable | TODO | |
| Metric open questions listed | TODO | |

Decision rule: FAIL if final KPIs are claimed without definitions or evidence.

## 10. Recommended Medallion Direction

| Check | Status | Evidence / Notes |
|---|---|---|
| Source layer direction exists | TODO | |
| Bronze/staging direction exists | TODO | |
| Silver/intermediate direction exists | TODO | |
| Gold/star schema direction exists | TODO | |
| Semantic/analytics direction exists | TODO | |
| Presentation direction exists | TODO | |
| Risks and dependencies listed | TODO | |

Decision rule: FAIL if later-layer direction is disconnected from discovery findings.

## 11. SQL Proof Evidence

| Check | Status | Evidence / Notes |
|---|---|---|
| SQL proof files exist for source inventory | TODO | |
| SQL proof files exist for row counts | TODO | |
| SQL proof files exist for key checks | TODO | |
| SQL proof files exist for duplicate checks | TODO | |
| SQL proof files exist for relationship checks | TODO | |
| SQL proof files exist for orphan checks | TODO | |
| SQL proof files include captured results | TODO | |
| SQL proof files include PASS/WARN/FAIL/BLOCKED status | TODO | |

Decision rule: FAIL if discovery claims are made without SQL evidence.

## 12. Open Questions and Blocked Scope

| Check | Status | Evidence / Notes |
|---|---|---|
| Open business questions listed | TODO | |
| Open technical questions listed | TODO | |
| Blocked scope listed | TODO | |
| Assumptions clearly separated from facts | TODO | |
| Required human decisions listed | TODO | |
| Requirements checkpoint question included | TODO | |

Decision rule: FAIL if uncertainty is hidden or the agent proceeds without approval.

## 13. Final Discovery Decision

Select one:

| Decision | Meaning |
|---|---|
| `APPROVED` | Discovery is complete. Continue to bootstrap/build. |
| `APPROVED WITH CONDITIONS` | Continue, but apply listed conditions as project rules. |
| `NOT APPROVED` | Do not continue. Fix discovery first. |

```text
Decision: TODO
Reason:
Required changes before next phase:
Approved project rules to carry forward:
```

## Required Updates After Checklist

After completing this checklist, update:

```text
reports/agent/PIPELINE_STATUS.md
reports/agent/CONTEXT_TREE.md
AGENT_PLAN.md
```

If any item is marked `FAIL` or `BLOCKED`, the agent must stop before bootstrap/build unless the data engineer explicitly approves the risk.
