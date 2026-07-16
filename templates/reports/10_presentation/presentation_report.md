# Presentation Layer Report

## Template Use

Use this file as the fixed structure for `reports/agent/10_presentation/presentation_report.md`.
Replace placeholders with presentation artifact, validation, and handoff evidence.

## Summary

- Status: <BLOCKED / IN PROGRESS / PASS / WARN / FAIL>
- Presentation state: <PRESENTATION_GENERATED / RUNTIME_PREFLIGHT_PENDING / BROWSER_VALIDATION_PENDING / MCP_REVIEW_PENDING / FINAL_VERIFICATION_PENDING / VERIFIED_FOR_HANDOFF / BLOCKED>
- Presentation technology: <Matplotlib web report / Power BI handoff / other>
- Report artifact: <generated / missing>
- Report access: <withheld until verification / VERIFIED_FOR_HANDOFF>
- Open instructions: <not available / command and URL>
- Artifact path: <path>
- Evidence: reports/agent/10_presentation/REPORT_HANDOFF_READINESS.json

Before verified handoff, do not publish report URLs, open commands, or “report ready” language.
Use: “Report artifacts were generated, but the report is not ready to open. Runtime and browser verification are still pending.”

## Scope Approved

| Scope item | Included | Evidence |
|---|---|---|
| Executive summary | <yes/no/deferred> | <path> |
| Key performance indicator cards | <yes/no/deferred> | <path> |
| Trends page | <yes/no/deferred> | <path> |
| Driver/segmentation pages | <yes/no/deferred> | <path> |
| Details or drill-through | <yes/no/deferred> | <path> |
| Report information page | <yes/no/deferred> | <path> |

## Validation

| Check | Result | Evidence |
|---|---|---|
| Manifest relation resolution | <PASS/WARN/FAIL/BLOCKED/NOT_RUN> | <path> |
| Runtime relation preflight | <PASS/WARN/FAIL/BLOCKED/NOT_RUN> | runtime_preflight.json |
| Initial live data load | <PASS/WARN/FAIL/BLOCKED/NOT_RUN> | /api/charts.json /api/metrics.json |
| Refresh endpoint | <PASS/WARN/FAIL/BLOCKED/NOT_RUN> | /api/refresh |
| Required KPI payloads | <PASS/WARN/FAIL/BLOCKED/NOT_RUN> | rendered_metric_manifest.json |
| Required chart payloads | <PASS/WARN/FAIL/BLOCKED/NOT_RUN> | chart_registry.json |
| Local server validation | <PASS/WARN/FAIL/BLOCKED/SKIPPED> | validate_local_web_report.py |
| Deterministic Playwright | <PASS/WARN/FAIL/BLOCKED/SKIPPED> | validate_live_report_dom.py |
| Actual Playwright MCP review | <PASS/WARN/FAIL/BLOCKED/SKIPPED> | LLM_PLAYWRIGHT_REVIEW.json |
| LLM review artifact validation | <PASS/WARN/FAIL/BLOCKED/SKIPPED> | check_llm_playwright_review.py |
| Independent verification | <PASS/WARN/FAIL/BLOCKED/NOT_RUN> | INDEPENDENT_VERIFICATION_REPORT.json |
| Final strict acceptance | <PASS/WARN/FAIL/BLOCKED/NOT_RUN> | ACCEPTANCE_GATE_REPORT.json |
| Handoff readiness | <PASS/FAIL> | REPORT_HANDOFF_READINESS.json |
| Open instructions released | <YES/NO> | YES only when handoff readiness PASS and open_allowed=true |

## Verified report handoff

Opening instructions are shown only after `REPORT_HANDOFF_READINESS.json` has `status=PASS` and `open_allowed=true`.

- Open instructions released: <YES/NO>
- Launcher: <open_report.bat / open_report.sh / not available>
- Verified URL: <url or withheld>

## Open Decisions

- <decision or "None">

## Next Action

- <runtime/browser verification / verified handoff / final delivery checkpoint>
