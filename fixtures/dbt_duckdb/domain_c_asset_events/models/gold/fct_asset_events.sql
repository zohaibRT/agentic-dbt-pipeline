select
    event_id,
    asset_id,
    status_code,
    status_name,
    event_date,
    signal_value,
    case when status_code = 'C' then 1 else 0 end as is_completed
from {{ ref('int_asset_events_enriched') }}
