select
    a.activity_id,
    a.person_id,
    a.organization_id,
    a.status_code,
    s.status_name,
    a.activity_date,
    a.amount
from {{ ref('stg_case_activities') }} a
left join {{ ref('stg_statuses') }} s on a.status_code = s.status_code
