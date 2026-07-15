select
    encounter_id,
    provider_id,
    location_id,
    status_code,
    cast(encounter_date as date) as encounter_date
from {{ ref('raw_encounters') }}
