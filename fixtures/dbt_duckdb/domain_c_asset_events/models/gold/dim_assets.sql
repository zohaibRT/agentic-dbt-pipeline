select asset_id, asset_name from {{ ref('stg_assets') }}
