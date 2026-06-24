# Warehouse Adapter Routing

Use the warehouse adapter selected by the active dbt profile. Do not probe unrelated warehouses.

## Core rule

Resolve the active warehouse in this order before discovery or dbt commands:

1. Load prompt values.
2. Load `.env`.
3. Resolve `DBT_PROFILE_NAME` / `dbt_profile_name`.
4. Read only that profile key from `~/.dbt/profiles.yml`.
5. Use that profile target's `type` as the warehouse adapter.

The selected dbt profile is the source of truth for discovery routing. If `.env` selects a PostgreSQL profile, use PostgreSQL discovery only. Do not call AWS, Redshift, Snowflake, BigQuery, Databricks, or connector-specific discovery paths unless the selected profile adapter is that warehouse type or the user explicitly asks for that warehouse.

## Adapter-specific discovery

Use the adapter from the selected profile:

| Profile `type` | Discovery path |
|---|---|
| `postgres` | Use PostgreSQL metadata queries through the dbt profile connection |
| `redshift` | Use Redshift metadata queries through the dbt profile connection |
| `snowflake` | Use Snowflake metadata queries through the dbt profile connection |
| `bigquery` | Use BigQuery metadata queries through the dbt profile connection |
| `databricks` | Use Databricks metadata queries through the dbt profile connection |

Do not use cloud account probes, identity calls, or external warehouse connectors as a fallback before checking the selected dbt profile adapter.

## Prohibited behavior

- Do not call AWS identity APIs when `.env` selects a PostgreSQL profile.
- Do not use Redshift discovery because a Redshift profile exists elsewhere in `profiles.yml`.
- Do not inspect sibling projects, prior workspaces, terminal history, or old `.env` files to choose a warehouse.
- Do not switch adapters because one connector has expired credentials.
- Do not summarize expired credentials for unrelated adapters unless the active selected profile uses that adapter.

## If the selected profile fails

If discovery fails against the selected profile:

1. Report the selected profile name and adapter.
2. Report the failed command or check.
3. Ask the user whether to fix that profile or choose a different profile.
4. Do not try another adapter automatically.

## User-facing explanation

When discovery starts, include a short line like:

```text
Using `.env` profile `<profile_name>` with adapter `<adapter_type>` for discovery. I will not query other warehouses unless you ask me to change profiles.
```
