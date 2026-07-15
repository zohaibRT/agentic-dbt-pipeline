select
    encounter_id as event_id,
    provider_id,
    location_id,
    status_code,
    status_name,
    encounter_date as event_date,
    case when status_code = 'C' then 1 else 0 end as is_completed
from {{ ref('int_encounters_enriched') }}
