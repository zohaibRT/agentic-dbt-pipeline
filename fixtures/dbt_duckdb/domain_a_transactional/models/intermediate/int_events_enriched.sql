select
    e.event_id,
    e.entity_id,
    e.item_id,
    e.status_code,
    s.status_name,
    e.event_date,
    e.amount
from {{ ref('stg_events') }} e
left join {{ ref('stg_statuses') }} s on e.status_code = s.status_code
