select item_id, item_name from {{ ref('raw_catalog_items') }}
