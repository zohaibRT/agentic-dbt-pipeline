# Report Handoff Readiness

- Status: PASS
- Presentation state: VERIFIED_FOR_HANDOFF
- Open allowed: True
- Report bundle hash: 75cd3c1aef66d875b060441beba46aadb195c195867020d15f78d0444674d832
- Reviewed at: 2026-07-16T22:28:28.472938+00:00

## Gates

| Gate | Status | Evidence | Notes |
|---|---|---|---|
| manifest_relation_resolution | PASS | C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events\reports\agent\10_presentation\matplotlib\runtime_preflight.json |  |
| runtime_preflight | PASS | validate_local_web_report.py / runtime_preflight.json |  |
| initial_data_load | PASS | live data endpoints |  |
| refresh_validation | PASS | refresh endpoint |  |
| deterministic_playwright | PASS | validate_live_report_dom.py |  |
| playwright_mcp_review | NOT_APPLICABLE |  | mcp_not_required_or_fixture_exempt |
| llm_review_artifact_validation | NOT_APPLICABLE |  | mcp_not_required_or_fixture_exempt |
| independent_verification | PASS | C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events\reports\agent\INDEPENDENT_VERIFICATION_REPORT.json |  |
| final_acceptance | PASS | C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events\reports\agent\ACCEPTANCE_GATE_REPORT.json |  |

## Verified report handoff

Opening instructions are released only when status is PASS and open_allowed is true.

Open instructions may be shown to the user.
- Suggested launcher: `reports/agent/10_presentation/matplotlib/open_report.bat`
- Verified URL: `http://127.0.0.1:8765/`

