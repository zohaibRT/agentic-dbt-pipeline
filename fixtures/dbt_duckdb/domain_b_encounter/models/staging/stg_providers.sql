select provider_id, provider_name from {{ ref('raw_providers') }}
