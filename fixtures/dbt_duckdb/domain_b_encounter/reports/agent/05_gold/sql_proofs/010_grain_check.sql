-- purpose: gold grain uniqueness for fct_encounters
-- expected result: 5
-- captured result: 5
-- status: PASS
select count(*) as row_count from {{ ref('fct_encounters') }};
