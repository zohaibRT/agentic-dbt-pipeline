# Report Handoff Readiness

- Status: PASS
- Presentation state: VERIFIED_FOR_HANDOFF
- Open allowed: True
- Report bundle hash: a30057a90223ca2e64bcd38d1d8abf3eac29d035c247fdcbb4b895f85f0e2993
- Reviewed at: 2026-07-17T05:32:47.232467+00:00

## Gates

| Gate | Status | Evidence | Notes |
|---|---|---|---|
| manifest_relation_resolution | PASS | C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_a_transactional\target\manifest.json |  |
| runtime_preflight | PASS | validate_local_web_report.py / runtime_preflight.json |  |
| initial_data_load | PASS | live data endpoints |  |
| refresh_validation | PASS | refresh endpoint |  |
| deterministic_playwright | PASS | validate_live_report_dom.py |  |
| playwright_mcp_review | PASS | C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_a_transactional\reports\agent\10_presentation\LLM_PLAYWRIGHT_REVIEW.json |  |
| llm_review_artifact_validation | PASS | check_llm_playwright_review.py |  |
| independent_verification | PASS | C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_a_transactional\reports\agent\INDEPENDENT_VERIFICATION_REPORT.json |  |
| final_acceptance | PASS | C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_a_transactional\reports\agent\ACCEPTANCE_GATE_REPORT.json |  |

## Verified report handoff

Opening instructions are released only when status is PASS and open_allowed is true.

Open instructions may be shown to the user.
- Suggested launcher: `reports/agent/10_presentation/matplotlib/open_report.bat`
- Verified URL: `http://127.0.0.1:8765/`

