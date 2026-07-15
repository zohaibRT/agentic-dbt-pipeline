select
    event_id,
    asset_id,
    status_code,
    cast(event_date as date) as event_date,
    cast(signal_value as double) as signal_value
from {{ ref('raw_asset_events') }}
