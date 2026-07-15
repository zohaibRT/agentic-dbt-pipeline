select
    activity_id as event_id,
    encounter_id,
    provider_id,
    location_id,
    activity_type,
    activity_date as event_date
from {{ ref('int_activities_enriched') }}
