-- purpose: gold grain uniqueness for fct_events
-- expected result: 5
-- captured result: 5
-- status: PASS
select count(*) as row_count from {{ ref('fct_events') }};
