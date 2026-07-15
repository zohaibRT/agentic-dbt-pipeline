select person_id, person_name from {{ ref('stg_people') }}
