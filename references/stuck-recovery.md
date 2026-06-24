# Stuck / Recovery Protocol

Use this whenever the agent is blocked, a shell command appears hung, validation fails repeatedly, or required input is missing.

Do not keep retrying blindly.

## Stop And Summarize

Report:

- Current phase
- Last successful command
- Failed or stuck command
- Error message or missing input
- Files changed so far
- `git status`

## Classify The Blocker

Use one of these labels:

- Missing dbt profile
- Wrong or missing `source_schema`
- Wrong or missing `source_name`
- Unclear `project_rules`
- dbt parse/build/test failure
- Long-running shell command
- Credentials or secret missing
- Git remote, commit, or push issue
- Agents Schema unsupported destination
- Source data missing or empty
- Wrong database, dataset, catalog, schema, table, tenant, client, domain, environment, or source assumption

## Try One Safe Recovery

Pick only one safe action before asking again:

- Run `dbt debug`
- Run `dbt parse --no-partial-parse`
- Run a scoped build: `dbt build --select +path:<layer_path>`
- Inspect available databases, datasets, catalogs, schemas, or table counts as metadata only
- Ask for the missing profile/schema/source/rule
- Skip optional CI or Agents Schema when running local-only

Metadata listing is not approval to switch. If the configured source is empty or a better candidate appears, stop and ask the user to approve the exact source before profiling rows, columns, keys, relationships, business entities, tenants, clients, domains, environments, or writing discovery files.

## Ask For A Decision

If the blocker remains, ask a short question with concrete options.

Examples:

```text
I cannot find source_schema: Source.
I found these schemas: analytics, raw_source, public.
Which schema should I use?
```

```text
The configured source schema is empty:
- Profile: zension_crm
- Database: dbt
- Source schema: source

I found a possible candidate from metadata only:
- Database/schema: zension.source
- Evidence: contains CRM-like tables

Should I switch to this candidate and run read-only discovery there?
```

```text
The command is still running:
dbt build --select +path:models/gold/hospital

Should I wait, stop it, or inspect logs in a new terminal?
```

```text
Agents Schema supports Snowflake, Databricks, and BigQuery.
The selected profile adapter is unsupported. Should I keep the workflow file but skip live sync?
```
