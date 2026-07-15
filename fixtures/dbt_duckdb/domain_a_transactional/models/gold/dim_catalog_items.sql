select item_id, item_name from {{ ref('stg_catalog_items') }}
