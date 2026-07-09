-- Assumption: {{ model }} stays one row per {{ grain_key }} after transformation.
-- Source evidence: reports/agent/<phase>/sql_proofs/030_<model>_grain_check.sql
select {{ grain_key }}, count(*) as row_count
from {{ ref('<model>') }}
group by {{ grain_key }}
having count(*) > 1
