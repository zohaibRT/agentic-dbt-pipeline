select organization_id, organization_name from {{ ref('raw_organizations') }}
