# Report Index

## Template Use

Use this file as the fixed structure for `reports/agent/REPORT_INDEX.md`.
Update it after every report is created or changed.

## Root Control Files

| File | Purpose | Status | What the data engineer should check |
|---|---|---|---|
| `reports/agent/PIPELINE_STATUS.md` | Current phase and checkpoint status | <status> | Confirm the active phase and approval gate |
| `reports/agent/CONTEXT_TREE.md` | Reusable project context and decisions | <status> | Confirm decisions, open questions, and deferred scope |
| `reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md` | Requirement-to-artifact traceability | <status> | Confirm requirements have evidence and future verification paths |

## Discovery Reports

| Report | Purpose | Status | What the data engineer should check |
|---|---|---|---|
| `reports/agent/00_discovery/discovery_report.md` | Source discovery conclusions and recommended medallion direction | <status> | Check source evidence, relationships, risks, and recommendation |
| `reports/agent/00_discovery/requirements.md` | Source-derived project requirements | <status> | Check inferred requirements, confidence, and open questions |
| `reports/agent/00_discovery/cardinality_report.md` | Join safety and cardinality evidence | <status> | Check row multiplication, bridge risk, and unsafe joins |
| `reports/agent/00_discovery/relationship_profile.md` | Relationship evidence and entity relationship diagram | <status> | Check proven versus uncertain relationships |
| `reports/agent/00_discovery/DISCOVERY_APPROVAL_CHECKLIST.md` | Discovery readiness gate | <status> | Confirm approval decision and conditions |
| `reports/agent/00_discovery/sql_proofs/` | Runnable discovery evidence queries | <status> | Re-run key proof files if needed |

## Later Phase Reports

| Phase | Report | Status | Notes |
|---|---|---|---|
| Project setup and configuration | `reports/agent/01_setup/setup_report.md` | PENDING | Not created by discovery unless setup has run |
| Sources | `reports/agent/02_sources/sources_report.md` | PENDING | Requires separate approval |
| Bronze / staging | `reports/agent/03_bronze/bronze_report.md` | PENDING | Requires separate approval |
| Silver / intermediate | `reports/agent/04_silver/silver_report.md` | PENDING | Requires separate approval |
| Gold / marts | `reports/agent/05_gold/gold_report.md` | PENDING | Requires separate approval |
| Semantic layer | `reports/agent/06_semantic/semantic_report.md` | PENDING | Requires separate approval |
| Project evaluator | `reports/agent/07_evaluator/evaluator_report.md` | PENDING | Requires separate approval |
| Documentation | `reports/agent/08_documentation/docs_report.md` | PENDING | Requires separate approval |
| Analytics insight reporting | `reports/agent/09_analytics_insights/analytics_insight_report.md` | PENDING | Requires separate approval |
| Presentation layer | `reports/agent/10_presentation/presentation_report.md` | PENDING | Requires separate approval |
