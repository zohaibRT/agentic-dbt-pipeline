# Independent Verification Report

**Overall status:** PASS
**Checked at:** 2026-07-16T22:26:20.354336+00:00
**Project root:** `C:\codebase\agentic-dbt-pipeline\fixtures\dbt_duckdb\domain_b_encounter`
**Mode:** `independent`

## Local recalculation

| Check | Status | Detail |
|---|---|---|
| manifest_inventory | PASS | resources=34 |
| detect_builder_false_pass | PASS | checked=2 false_pass=0 |
| synthetic_approval_path_guard | PASS | fixture path — synthetic approval evidence permitted |
| no_fixed_count_gates | PASS | no arbitrary fixed-count gates |

## Validator Results

| Script | Category | Status | Exit Code |
|---|---|---|---|
| check_model_classification_coverage.py | manifest_inventory_classification | PASS | 0 |
| check_fact_analytical_coverage.py | fact_coverage | PASS | 0 |
| check_metric_contract_completeness.py | kpi_contract_completeness | PASS | 0 |
| verify_metric_reconciliation.py | numeric_and_set_reconciliation | PASS | 0 |
| check_human_approval_coverage.py | human_approval_coverage | PASS | 0 |
| check_time_intelligence_coverage.py | time_intelligence_coverage | PASS | 0 |
| check_data_observability_coverage.py | observability_coverage | PASS | 0 |
| check_exposure_coverage.py | exposure_coverage | PASS | 0 |
| check_report_page_contracts.py | page_contracts | PASS | 0 |
| check_presentation_traceability.py | visual_traceability_proof_mapping | PASS | 0 |
| validate_rendered_report_content.py | rendered_values | PASS | 0 |
| validate_chart_registry.py | chart_registry_proof_mapping | PASS | 0 |
| check_report_business_readability.py | technical_labels_not_visible | WARN | 0 |
| validate_kpi_proofs.py | proof_mapping | WARN | 0 |
| check_layer_proof_coverage.py | layer_proof_mapping | PASS | 0 |
| check_requirement_traceability.py | requirement_traceability | PASS | 0 |
| check_presentation_coverage.py | presentation_coverage | PASS | 0 |
| validate_live_report_dom.py | live_browser_behavior | PASS | 0 |

## Failures

- None

## Notes

- Fresh process; no builder chat context.
- Synthetic fixture approvals must not appear outside `fixtures/`.
