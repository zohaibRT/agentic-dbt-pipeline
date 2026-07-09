-- Assumption: stored measure in {{ dimension_model }} must match a fresh recomputation from {{ fact_model }}.
-- Source evidence: reports/agent/<phase>/sql_proofs/050_<dimension_model>_cross_check.sql
select d.{{ dimension_key }}, d.{{ stored_measure }}, o.computed_total
from {{ ref('<dimension_model>') }} d
join (
    select {{ dimension_key }}, sum({{ amount_column }}) as computed_total
    from {{ ref('<fact_model>') }}
    group by {{ dimension_key }}
) o on d.{{ dimension_key }} = o.{{ dimension_key }}
where abs(d.{{ stored_measure }} - o.computed_total) > 0.01
