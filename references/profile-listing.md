# Profile Listing

Use this when `DBT_PROFILE_NAME` / `dbt_profile_name` is missing, ambiguous, invalid, or when the user asks which dbt profiles are available.

## Core rule

List available dbt profiles to help the data engineer choose. Do not choose a profile for the user.

Reading `~/.dbt/profiles.yml` for this purpose is allowed before discovery because it is local configuration inspection, not warehouse access. Do not run `dbt debug`, call cloud identity checks, query warehouses, or probe connectors while listing profiles.

When the agent UI supports a user-question or choice prompt, prefer that over a plain paragraph. Ask one clear question:

```text
Which dbt profile should this pipeline use?
```

Use the help text:

```text
Select the warehouse connection for discovery and builds.
```

Each choice label should include the profile key, adapter, database or database-equivalent, and profile schema. Include an "Other" or free-form option when available. The question must not preselect a profile unless the user already supplied `DBT_PROFILE_NAME`.

## What to show

Show a concise table:

| Profile | Adapter | Notes |
|---|---|---|
| `<profile_key>` | `<adapter_type>` | `<non-secret host kind or host> / <target schema>` |

Safe note fields:

- Adapter type from the selected target output, such as PostgreSQL, Redshift, Snowflake, BigQuery, or Databricks.
- Host kind or host when it is not a secret, such as `localhost`, `serverless`, or a non-password hostname.
- Database name, database name equivalent, or dataset name when useful.
- Target schema.
- Target name, such as `dev`, when useful.

Do not show:

- Passwords or `pass` values.
- Tokens, private keys, account keys, secret environment variable values, or connection strings containing credentials.
- Full `profiles.yml`.
- Usernames when avoidable; show them only if the user explicitly asks and they are not sensitive in that environment.

## User-facing wording

When `.env` is missing or `DBT_PROFILE_NAME` is missing, use this shape:

```text
I did not find a selected dbt profile yet.

Question: Which dbt profile should this pipeline use?
Help: Select the warehouse connection for discovery and builds.

| Profile | Adapter | Notes |
|---|---|---|
| jaffle_shop | PostgreSQL | localhost / ecommerce |
| poc_project | Redshift | serverless / raw |

Please tell me which `DBT_PROFILE_NAME` to use, plus `DBT_DOMAIN` and `DBT_SOURCE_SCHEMA`.
I will not choose one automatically.
```

If the profile file cannot be read, say that clearly and ask the user to provide `DBT_PROFILE_NAME`.

## Notes formatting

Prefer short, human-friendly notes:

- `localhost / ecommerce`
- `serverless / raw`
- `analytics database / reporting`
- `BigQuery dataset / analytics`

If the host is long, reduce it to a useful safe label such as `serverless`, `remote host`, or the database name plus schema.

## Important boundary

Profile listing does not establish the discovery route. The route is locked only after the user selects `DBT_PROFILE_NAME`, the agent reads that selected profile target, and the agent announces the selected profile and adapter according to [warehouse-adapter-routing.md](warehouse-adapter-routing.md).
