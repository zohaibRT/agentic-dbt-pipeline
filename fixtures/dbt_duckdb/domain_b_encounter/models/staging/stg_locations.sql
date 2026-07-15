select location_id, location_name from {{ ref('raw_locations') }}
