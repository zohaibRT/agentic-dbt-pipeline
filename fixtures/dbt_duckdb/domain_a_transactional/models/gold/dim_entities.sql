select entity_id, entity_name from {{ ref('stg_entities') }}
