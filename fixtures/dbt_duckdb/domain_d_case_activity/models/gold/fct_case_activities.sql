select
    activity_id as event_id,
    person_id,
    organization_id,
    status_code,
    status_name,
    activity_date as event_date,
    amount,
    case when status_code = 'C' then 1 else 0 end as is_completed
from {{ ref('int_case_activities_enriched') }}
