-- Assumption: joining into {{ model }} must not multiply or drop rows versus {{ upstream_model }}.
-- Source evidence: reports/agent/<phase>/sql_proofs/020_<model>_upstream_row_count_compare.sql
with base as (
    select count(*) as row_count from {{ ref('<upstream_model>') }}
),
joined as (
    select count(*) as row_count from {{ ref('<model>') }}
)
select base.row_count as before_join, joined.row_count as after_join
from base, joined
where base.row_count != joined.row_count
