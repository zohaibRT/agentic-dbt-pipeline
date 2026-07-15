select
    e.event_id,
    e.asset_id,
    e.status_code,
    s.status_name,
    e.event_date,
    e.signal_value
from {{ ref('stg_asset_events') }} e
left join {{ ref('stg_statuses') }} s on e.status_code = s.status_code
