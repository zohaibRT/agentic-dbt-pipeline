{% snapshot activity_events_scd %}
{{
  config(
    target_schema='snapshots',
    unique_key='activity_id',
    strategy='check',
    check_cols=['activity_type', 'activity_date']
  )
}}
select
    activity_id,
    encounter_id,
    activity_type,
    activity_date
from {{ ref('stg_activities') }}
{% endsnapshot %}
