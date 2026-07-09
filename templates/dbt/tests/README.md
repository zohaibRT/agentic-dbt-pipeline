# dbt Assumption Test Templates

Copy these into the generated dbt project's `tests/` folder and replace placeholders.

Naming convention:

```text
tests/assert_<model>_<assumption_slug>.sql
```

Required placeholders to replace:

- `<model>`
- `<grain_key>`
- `<upstream_model>`
- `<status_value>`
- `<required_field>`
- `<header_model>`, `<detail_model>`, `<header_total_column>`, `<detail_amount_column>`
- `<dimension_model>`, `<fact_model>`, `<dimension_key>`, `<stored_measure>`, `<amount_column>`
- `<earlier_date_column>`, `<later_date_column>`

Pair every promoted test with a warehouse proof in the matching phase `sql_proofs/` folder.
