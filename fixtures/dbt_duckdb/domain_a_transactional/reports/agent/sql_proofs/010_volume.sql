-- purpose: volume KPI proof for KPI-001
-- kpi_id: KPI-001
-- validation_type: numeric_tolerance
-- expected result: 5
-- captured result: 5
-- tolerance: 0
-- technical_verification_status: PASS
-- status: PASS
select count(*) as volume from {{ ref('fct_events') }};
