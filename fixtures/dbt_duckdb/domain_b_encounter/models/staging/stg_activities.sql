select
    activity_id,
    encounter_id,
    provider_id,
    location_id,
    activity_type,
    cast(activity_date as date) as activity_date
from {{ ref('raw_activities') }}
