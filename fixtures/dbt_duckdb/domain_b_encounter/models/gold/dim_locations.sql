select location_id, location_name from {{ ref('stg_locations') }}
