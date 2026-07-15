select
    event_id,
    entity_id,
    item_id,
    status_code,
    cast(event_date as date) as event_date,
    cast(amount as double) as amount
from {{ ref('raw_events') }}
