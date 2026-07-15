select asset_id, asset_name from {{ ref('raw_assets') }}
