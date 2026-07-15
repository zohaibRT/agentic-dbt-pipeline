select
    e.encounter_id,
    e.provider_id,
    e.location_id,
    e.status_code,
    s.status_name,
    e.encounter_date
from {{ ref('stg_encounters') }} e
left join {{ ref('stg_statuses') }} s on e.status_code = s.status_code
