# Report Index

## Template Use

Use this file as the fixed structure for `reports/agent/REPORT_INDEX.md`.
Update it after every report is created or changed.

**Status rule:** Never write `WARN`, `FAIL`, `BLOCKED`, or `SKIPPED` without filling **Why this status was used**.  
If someone asks “why is this WARN?”, this file must already contain the answer.

Status meanings: `PASS` = ready; `WARN` = usable with a documented limitation; `FAIL` = unsafe/wrong; `BLOCKED` = waiting on input; `SKIPPED` = intentionally not run; `PENDING` / `NOT APPROVED` = not finished yet.

## Root Control Files

| File | Purpose | Status | Why this status was used | What the data engineer should check |
|---|---|---|---|---|
| `reports/agent/PIPELINE_STATUS.md` | Current phase and checkpoint status | <status> | <one-sentence reason, or "All checks PASS"> | Confirm the active phase and approval gate |
| `reports/agent/CONTEXT_TREE.md` | Reusable project context and decisions | <status> | <one-sentence reason> | Confirm decisions, open questions, and deferred scope |
| `reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md` | Requirement-to-artifact traceability | <status> | <one-sentence reason> | Confirm requirements have evidence and future verification paths |

## Discovery Reports

| Report | Purpose | Status | Why this status was used | What the data engineer should check |
|---|---|---|---|---|
| `reports/agent/00_discovery/discovery_report.md` | Source discovery conclusions and recommended medallion direction | <status> | <e.g. Privacy, relationship, date, or amount conditions remain open> | Check source evidence, relationships, risks, and recommendation |
| `reports/agent/00_discovery/requirements.md` | Source-derived project requirements | <status> | <e.g. Open business decisions still need approval> | Check inferred requirements, confidence, and open questions |
| `reports/agent/00_discovery/core_profile.json` | Non-secret run context | <status> | <e.g. Context captured; human must confirm profile/source lock> | Confirm profile, adapter, database, and source schema |
| `reports/agent/00_discovery/discovery_raw.json` | Structured evidence for all tables | <status> | <e.g. Inclusion complete; deep detail limited to priority tables> | Confirm inclusion reasons and proof linkage |
| `reports/agent/00_discovery/first_pass_scope.json` | Locked first-pass included table set | <status> | <e.g. proposed until discovery approval> | Confirm included list matches business first-pass scope |
| `reports/agent/00_discovery/cardinality_report.md` | Join safety and cardinality evidence | <status> | <e.g. Orphans or row-multiplication risks documented> | Check row multiplication, bridge risk, and unsafe joins |
| `reports/agent/00_discovery/relationship_profile.md` | Relationship evidence and entity relationship diagram | <status> | <e.g. Some joins uncertain or cross-system blocked> | Check proven versus uncertain relationships |
| `reports/agent/00_discovery/DISCOVERY_APPROVAL_CHECKLIST.md` | Discovery readiness gate | <status> | <e.g. Waiting for human approval> | Confirm approval decision and conditions |
| `reports/agent/00_discovery/sql_proofs/` | Runnable discovery evidence queries | <status> | <e.g. Proofs captured; some proofs themselves WARN> | Re-run key proof files if needed |

## Later Phase Reports

| Phase | Report | Status | Why this status was used | Notes |
|---|---|---|---|---|
| Project setup and configuration | `reports/agent/01_setup/setup_report.md` | PENDING | Phase not started or not approved yet | Requires discovery approval for automatic setup |
| Sources | `reports/agent/02_sources/sources_report.md` | PENDING | Phase not started or not approved yet | Requires separate approval |
| Bronze / staging | `reports/agent/03_bronze/bronze_report.md` | PENDING | Phase not started or not approved yet | Requires separate approval |
| Silver / intermediate | `reports/agent/04_silver/silver_report.md` | PENDING | Phase not started or not approved yet | Requires separate approval |
| Gold / marts | `reports/agent/05_gold/gold_report.md` | PENDING | Phase not started or not approved yet | Requires separate approval |
| Semantic layer | `reports/agent/06_semantic/semantic_report.md` | PENDING | Phase not started or not approved yet | Requires separate approval |
| Project evaluator | `reports/agent/07_evaluator/evaluator_report.md` | PENDING | Phase not started or not approved yet | Requires separate approval |
| Documentation | `reports/agent/08_documentation/docs_report.md` | PENDING | Phase not started or not approved yet | Requires separate approval |
| Analytics insight reporting | `reports/agent/09_analytics_insights/analytics_insight_report.md` | PENDING | Phase not started or not approved yet | Requires separate approval |
| Presentation layer | `reports/agent/10_presentation/presentation_report.md` | PENDING | Phase not started or not approved yet | Requires separate approval |
