-- purpose: volume KPI
-- expected result: 5
-- captured result: 5
-- status: PASS
select count(*) as volume from {{ ref('fct_events') }};
