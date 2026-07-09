-- Assumption: rows with status '<status_value>' must have {{ required_field }} populated.
-- Source evidence: reports/agent/<phase>/sql_proofs/030_<model>_<required_field>_distribution.sql
select {{ grain_key }}, status, {{ required_field }}
from {{ ref('<model>') }}
where status = '<status_value>'
  and {{ required_field }} is null
