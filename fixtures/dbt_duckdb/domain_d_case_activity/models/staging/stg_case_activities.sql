select
    activity_id,
    person_id,
    organization_id,
    status_code,
    cast(activity_date as date) as activity_date,
    cast(amount as double) as amount
from {{ ref('raw_case_activities') }}
