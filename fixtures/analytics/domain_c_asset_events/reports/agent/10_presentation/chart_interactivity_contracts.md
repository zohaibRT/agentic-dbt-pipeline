# Chart Interactivity Contracts (TEST FIXTURE)

| Chart ID | Visual ID | Page | Chart Type | Metric IDs | Proof IDs | Hover Fields | Validation |
|---|---|---|---|---|---|---|---|
| volume_trend | visual_volume_trend | executive_overview | line | KPI-001 | PROOF-010_volume | metric_display_name, series_display_name, period_label, formatted_value, unit, currency, prior_formatted_value, abs_change_formatted, pct_change_formatted, target_formatted, target_variance_formatted, status_label, partial_period_note, freshness_timestamp, metric_definition_link | PASS |
| completion_rate_trend | visual_completion_rate_trend | executive_overview | bar | KPI-002 | PROOF-020_rate | metric_display_name, series_display_name, period_label, formatted_value, unit, currency, prior_formatted_value, abs_change_formatted, pct_change_formatted, target_formatted, target_variance_formatted, status_label, partial_period_note, freshness_timestamp, metric_definition_link | PASS |

## Metric manifest mapping

| Metric ID | Display Name | Visual IDs | Proof IDs | Formatted Value | Trust | Business Approval |
|---|---|---|---|---|---|---|
| KPI-001 | Volume KPI | visual_volume_trend, card_volume | PROOF-010_volume | 100 | TRUSTED | APPROVED |
| KPI-002 | Completion rate KPI | visual_completion_rate_trend, card_completion | PROOF-020_rate | 80.0% | TRUSTED | APPROVED |
| KPI-PENDING-001 | Draft exploratory metric |  |  | Pending | DRAFT | PENDING |
