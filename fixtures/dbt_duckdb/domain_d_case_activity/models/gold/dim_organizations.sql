select organization_id, organization_name from {{ ref('stg_organizations') }}
