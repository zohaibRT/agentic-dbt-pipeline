-- Assumption: {{ later_date_column }} must never be earlier than {{ earlier_date_column }}.
-- Source evidence: reports/agent/<phase>/sql_proofs/040_<model>_date_coverage.sql
select {{ grain_key }}, {{ earlier_date_column }}, {{ later_date_column }}
from {{ ref('<model>') }}
where {{ later_date_column }} < {{ earlier_date_column }}
