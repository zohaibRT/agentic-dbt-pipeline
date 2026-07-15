select provider_id, provider_name from {{ ref('stg_providers') }}
