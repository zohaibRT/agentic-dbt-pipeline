select entity_id, entity_name from {{ ref('raw_entities') }}
