-- purpose: gold grain uniqueness for fct_asset_events
-- expected result: 5
-- captured result: 5
-- status: PASS
select count(*) as row_count from {{ ref('fct_asset_events') }};
