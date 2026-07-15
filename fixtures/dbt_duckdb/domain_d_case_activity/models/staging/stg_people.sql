select person_id, person_name from {{ ref('raw_people') }}
