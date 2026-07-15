# Acceptance Gate Report

Overall status: **PASS**
Phase: **final**
Warning policy enforced: **yes**

## Check Results

| Check | Status | Detail |
|---|---|---|
| Required file: AGENT_PLAN.md | PASS | exists |
| Required file: reports/agent/00_discovery/core_profile.json | PASS | exists |
| Required file: reports/agent/00_discovery/discovery_raw.json | PASS | exists |
| Required file: reports/agent/00_discovery/requirements.md | PASS | exists |
| Required file: reports/agent/PIPELINE_STATUS.md | PASS | exists |
| Required file: reports/agent/CONTEXT_TREE.md | PASS | exists |
| Required file: reports/agent/REPORT_INDEX.md | PASS | exists |
| Required file: reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md | PASS | exists |
| Required file: reports/agent/LAYER_VERIFICATION_LEDGER.md | PASS | exists |
| Required file: reports/agent/KPI_DEFINITION_CONTRACTS.md | PASS | exists |
| Required file: reports/agent/METRIC_VERIFICATION_MATRIX.md | PASS | exists |
| PIPELINE_STATUS.md | PASS | no FAIL/BLOCKED status found |
| Phase report: reports/agent/03_bronze/bronze_report.md | PASS | required sections present |
| Phase report: reports/agent/04_silver/silver_report.md | PASS | required sections present |
| Phase report: reports/agent/05_gold/gold_report.md | PASS | required sections present |
| SQL proof files | PASS | 6 proof files have usable status/header evidence |
| Requirements traceability matrix | PASS | exists |
| Layer verification ledger | PASS | exists |
| KPI definition contracts | PASS | exists |
| Metric verification matrix | PASS | exists |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\check_discovery_artifacts.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events | PASS | Discovery artifact validation passed |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\check_gold_star_shape.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events | PASS | Models root: C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events\models\gold Facts: 1 \| Dimensions: 2 \| Bridges: 0 Fact models: fct_asset_events Dimension models: dim_assets, dim_statuses PASS \| gold/marts has both facts and dimensions |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\validate_kpi_proofs.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events | PASS | Optional catalogs present: dimension_catalog.md KPI proof validation summary:   measures: 6   metrics: 8   kpis: 2   sql proof files: 2   referenced proofs: 0 WARN: Catalogs do not reference sql_proofs/*.sql paths explicitly KPI proof validation PASSED with warnings |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\check_requirement_traceability.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events | PASS | Requirement traceability summary:   requirements checked: 5   warnings: 0   errors: 0 |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\check_layer_proof_coverage.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events | PASS | Layer proof coverage summary:   rows checked: 7   warnings: 0   errors: 0 |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\verify_metric_reconciliation.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events | PASS | Detected KPI contract schema: expanded Metric reconciliation summary:   KPI contract schema: expanded   KPI contracts checked: 2   metric matrix rows checked: 2   blocked/deferred KPIs: 0   critical reconciliation coverage: 2/2 (100%)   matrix reconciled: 2/2   warnings: 0   errors: 0 |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\check_model_classification_coverage.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events --phase final | PASS | Model classification (manifest): classified=7/7 (100%) unique_id_denominator=yes Model classification coverage check PASSED |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\check_analytics_coverage.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events | PASS | Analytics product coverage (informational counts only): gold_facts~1, business_measures~6, business_metrics~4, quality_metrics~2, pipeline_metrics~2, coverage_matrix=1/1, fact_contracts=1/1 Business-process coverage: 100% (required >= 90%) Fact analytical coverage: 100% (required >= 100%) Time-intelligence coverage: 100% (required >= 80%) Observability domain coverage: 100% (required >= 100%) Report traceability (RENDERED->proof): 100% (required >= 100%) Policy critical_reconciliation_coverage_r... |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\check_analytics_product_completeness.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events | PASS | Business-process coverage: PASS=1/1 (100%) Process module coverage: 1/1 (100%) Analytics product completeness check PASSED |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\check_fact_analytical_coverage.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events | PASS | Fact coverage contracts: rows=1, gold_facts=1, unique_ids=1 Critical fact coverage: 1/1 (100%) Fact analytical coverage check PASSED |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\check_metric_contract_completeness.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events | PASS | Metric contract completeness: schema=expanded contract_rows=2 Critical KPI contract coverage: 2/2 (100%) Metric contract completeness check PASSED |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\check_human_approval_coverage.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events --phase final | PASS | Human approval coverage: 2/2 (phase=final) Human approval coverage check PASSED |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\check_time_intelligence_coverage.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events | PASS | Time intelligence coverage: supported=8, applicable=8 (100%) Time intelligence coverage check PASSED |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\check_data_observability_coverage.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events | PASS | Observability domain coverage: 18/18 (100%) Data observability coverage check PASSED |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\check_presentation_coverage.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events | PASS | Presentation coverage: measures~6, metrics~4, kpis~2; RENDERED/TRUSTED=3; gold_facts~1 Rendered proof coverage: 3/3 (100%) Presentation coverage check PASSED |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\check_report_page_contracts.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events --phase final | PASS | Report page contracts: rows=6, rendered_pages~13 Report page contract field coverage: 6/6 (100%) Report page contracts check PASSED |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\check_report_business_readability.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events | PASS | Business readability: files=12, tech_name_hits~911, dim_row_count_hits~0, raw_float_hits~245, display_hints=True, label_coverage=100% (required=100%) WARN: high-precision raw floats present â€” ensure UI shows formatted_value (%, currency, rounded decimals) Report business readability check PASSED with warnings |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\check_exposure_coverage.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events --phase final | PASS | Exposure discovery: source=manifest inventory=manifest count=1 Production exposure coverage: 1/1 (100%) Exposure coverage check PASSED |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\check_presentation_hardcodes.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events | PASS | Checked 4 presentation Python file(s) Presentation hardcode check PASSED |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\check_privacy_opt_out.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events | PASS | SKIPPED: no recorded privacy minimization opt-out in requirements/context/plan |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\check_domain_neutrality.py --root C:\codebase\agentic-dbt-pipeline | PASS | Domain neutrality scan: root=C:\codebase\agentic-dbt-pipeline, files=246 Domain neutrality check PASSED |
| Validation script: validate_powerbi_pbip.py | SKIPPED | no PBIP found |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\validate_local_web_report.py --report-dir C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events/reports/agent/10_presentation/matplotlib | PASS | Local web report validation passed: http://127.0.0.1:61320/ returned 47122 bytes of HTML. |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\validate_rendered_report_content.py --report-dir C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events/reports/agent/10_presentation/matplotlib | PASS | Rendered report content scan: errors=0 Rendered report content validation PASSED |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\validate_chart_registry.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events | PASS | Chart registry validation: charts=2 errors=0 Chart registry validation PASSED |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\check_presentation_traceability.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events --phase final | PASS | Presentation traceability: metrics=3 visuals~8 proofs~2 errors=0 WARN: metric KPI-PENDING-001: no visual_ids/chart_ids/card_ids mapped WARN: metric KPI-PENDING-001: missing query_id mapping Presentation traceability check PASSED with warnings |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\validate_live_report_dom.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events --desktop --tablet --mobile --allow-skip | PASS | Wrote C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events\reports\agent\10_presentation\LIVE_REPORT_DOM_REPORT.json Wrote C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events\reports\agent\10_presentation\LIVE_REPORT_DOM_REPORT.md Live report DOM validation PASSED |
| C:\Program Files\Python312\python.exe C:\codebase\agentic-dbt-pipeline\scripts\run_independent_verifier.py --root C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_c_asset_events --skip-live | PASS | check_model_classification_coverage.py: PASS (exit 0) check_fact_analytical_coverage.py: PASS (exit 0) check_metric_contract_completeness.py: PASS (exit 0) verify_metric_reconciliation.py: PASS (exit 0) check_human_approval_coverage.py: PASS (exit 0) check_time_intelligence_coverage.py: PASS (exit 0) check_data_observability_coverage.py: PASS (exit 0) check_exposure_coverage.py: PASS (exit 0) check_report_page_contracts.py: PASS (exit 0) check_presentation_traceability.py: PASS (exit 0) validate... |
| dbt commands | SKIPPED | --skip-dbt was used |
| Production schedule / CI | PASS | relevant CI/orchestration evidence: fixture_ci.yml (acceptance_gate, analytics_gates, build_dbt_duckdb, unittest) |

## Warning acceptance

| Warning ID | Accepted | Detail |
|---|---|---|
| _none_ | — | — |

## Failures

- None

## Warnings

- None

## Recommended next action

Gate passed. Proceed to human sign-off and final delivery.
