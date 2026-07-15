select
    a.activity_id,
    a.encounter_id,
    a.provider_id,
    a.location_id,
    a.activity_type,
    a.activity_date,
    s.status_name
from {{ ref('stg_activities') }} a
left join {{ ref('stg_encounters') }} e on a.encounter_id = e.encounter_id
left join {{ ref('stg_statuses') }} s on e.status_code = s.status_code
