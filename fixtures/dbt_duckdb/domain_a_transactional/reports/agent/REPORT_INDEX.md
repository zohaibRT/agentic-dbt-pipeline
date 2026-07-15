# Report Index (TEST FIXTURE ONLY)

## Root Control Files

| File | Purpose | Status | Why this status was used | What the data engineer should check |
|---|---|---|---|---|
| `reports/agent/PIPELINE_STATUS.md` | Phase status | PASS | All fixture phases complete | Confirm PASS rows |
| `reports/agent/CONTEXT_TREE.md` | Context | PASS | Fixture context locked | Confirm profile/schema |
| `reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md` | Traceability | PASS | Requirements mapped | Confirm proof links |

## Discovery Reports

| Report | Purpose | Status | Why this status was used | What the data engineer should check |
|---|---|---|---|---|
| `reports/agent/00_discovery/discovery_report.md` | Discovery summary | PASS | Seeds inventoried | Review inclusion |
| `reports/agent/00_discovery/requirements.md` | Requirements | PASS | Derived from seeds | Approve scope |
| `reports/agent/00_discovery/core_profile.json` | Profile snapshot | PASS | Non-secret context | Confirm adapter |
| `reports/agent/00_discovery/discovery_raw.json` | Raw evidence | PASS | Linked proofs | Confirm tables |
| `reports/agent/00_discovery/sql_proofs/` | Discovery proofs | PASS | Runnable SQL | Re-run inventory |

## Later Phase Reports

| Phase | Report | Status | Why this status was used | Notes |
|---|---|---|---|---|
| Bronze / staging | `reports/agent/03_bronze/bronze_report.md` | PASS | Staging validated | Fixture |
| Silver / intermediate | `reports/agent/04_silver/silver_report.md` | PASS | Joins validated | Fixture |
| Gold / marts | `reports/agent/05_gold/gold_report.md` | PASS | Star schema validated | Fixture |
| Presentation layer | `reports/agent/10_presentation/presentation_report.md` | PASS | Charts rendered | Fixture |
