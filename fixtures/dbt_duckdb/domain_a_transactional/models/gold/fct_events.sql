select
    event_id,
    entity_id,
    item_id,
    status_code,
    status_name,
    event_date,
    amount,
    case when status_code = 'C' then 1 else 0 end as is_completed
from {{ ref('int_events_enriched') }}
