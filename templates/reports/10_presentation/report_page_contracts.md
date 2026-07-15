# Report Page Contracts

Pages are generated from discovered processes and metric families — not hardcoded industry titles.

Use stable `page_id` values. Display names may change without breaking traceability.

| Page ID | Page Name | Page Class | Audience | Business Processes | Business Questions | Decisions Supported | Primary KPIs | Driver Metrics | Guardrail Metrics | Dimensions | Filters | Reporting Period | Visuals | Exceptions | Insight Narrative | Recommended Actions | Caveats | Technical Validation Status | Business Approval Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| executive_overview | Executive Overview | executive_overview | leadership | <processes> | <questions> | <decisions> | <kpi_ids> | <driver_ids> | <guardrail_ids or NOT_APPLICABLE: reason> | <dims> | <filters> | <period or All time> | <visual_ids> | <exceptions> | <insight> | <actions or Business input required> | <caveats> | PASS/WARN/BLOCKED | APPROVED/PENDING_REVIEW/... |

Generic page classes (create only when evidence supports them): executive_overview, process_performance, trend_variance, segment_performance, lifecycle_status, exceptions_quality, pipeline_health, dimension_explorer, detail_drilldown, metric_dictionary, report_information.

Technical validation and business approval are separate. Do not treat SQL proof PASS as business APPROVED.
