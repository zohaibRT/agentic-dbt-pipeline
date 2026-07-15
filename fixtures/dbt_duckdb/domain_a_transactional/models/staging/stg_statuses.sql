select status_code, status_name from {{ ref('raw_statuses') }}
