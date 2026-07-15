select status_code, status_name from {{ ref('stg_statuses') }}
