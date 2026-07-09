-- Assumption: header total in {{ header_model }} must equal the sum of detail rows in {{ detail_model }}.
-- Source evidence: reports/agent/<phase>/sql_proofs/050_<header_model>_detail_reconciliation.sql
select
    h.{{ grain_key }},
    h.{{ header_total_column }},
    sum(d.{{ detail_amount_column }}) as detail_total
from {{ ref('<header_model>') }} h
join {{ ref('<detail_model>') }} d on h.{{ grain_key }} = d.{{ grain_key }}
group by h.{{ grain_key }}, h.{{ header_total_column }}
having abs(h.{{ header_total_column }} - sum(d.{{ detail_amount_column }})) > 0.01
