# Agents Schema Setup

Use Agents Schema to publish dbt metadata into the warehouse so agents can query project context from `AGENTS.*` before answering questions or writing SQL.

Agents Schema complements dbt project files. It does not replace editing-time context such as `dbt_project.yml`, model SQL, source YAML, or `manifest.json`. Use it as the warehouse-side metadata layer after the dbt project has been built and documented.

## What It Gives The Agent

- Queryable dbt model metadata in the warehouse
- Model and semantic object descriptions
- A standard `AGENTS` schema for discovery
- Context for agents that start from warehouse SQL rather than from local files
- A safer way to answer questions using known metadata instead of guessing

Example metadata table after sync:

```sql
select *
from AGENTS.DBT_MODEL;
```

## When To Run

Run Agents Schema after:

1. Sources, staging, intermediate, and marts exist.
2. Semantic layer YAML exists, when used.
3. `dbt docs generate` or `dbt parse` has produced `target/manifest.json`.
4. The dbt project has been committed or pushed to GitHub.

Do not run this before dbt metadata exists.

## Prerequisites

- [ ] `target/manifest.json` exists in the dbt project.
- [ ] The repository is connected to GitHub.
- [ ] The destination is supported by `dbt-labs/agents_schema`.
- [ ] GitHub secret `WAREHOUSE_CREDENTIALS` exists.
- [ ] The credentials can create and write to the configured Agents Schema destination.

Supported destinations:

- Snowflake
- Databricks
- BigQuery

## GitHub Secret

Add this GitHub Actions secret:

```text
WAREHOUSE_CREDENTIALS
```

Store destination credentials as YAML. Do not commit this file.

Snowflake example:

```yaml
type: snowflake
account: <account>
user: <user>
warehouse: <warehouse>
database: <database>
role: <role>
password: <password>
```

Databricks example:

```yaml
type: databricks
host: <workspace-host>
http_path: <sql-warehouse-http-path>
catalog: <catalog>
token: <token>
```

BigQuery example:

```yaml
type: bigquery
project_id: <project-id>
location: <location>
credentials_json:
  type: service_account
  project_id: <service-account-project>
  private_key_id: <private-key-id>
  private_key: <private-key>
  client_email: <client-email>
  client_id: <client-id>
```

## Workflow File

Create `.github/workflows/agents-schema-dbt.yml`:

```yaml
name: Agents Schema dbt

on:
  workflow_dispatch:
  push:
    branches: [main]
    paths:
      - '<project.root>/**'
      - '.github/workflows/agents-schema-dbt.yml'

jobs:
  agents-schema-dbt:
    uses: dbt-labs/agents_schema/.github/workflows/agents-schema-dbt.yml@v0.0.9
    with:
      dbt-project-dir: <project.root>
    secrets:
      WAREHOUSE_CREDENTIALS: ${{ secrets.WAREHOUSE_CREDENTIALS }}
```

Set `dbt-project-dir` to the folder that contains `dbt_project.yml`.

The reusable workflow expects the dbt manifest to be available in the repository:

```text
<project.root>/target/manifest.json
```

If the manifest is missing, generate it before the workflow runs:

```bash
dbt docs generate
```

When Agents Schema is enabled, commit only the manifest file from `target/`. Keep all other generated dbt artifacts ignored.

Recommended project `.gitignore` pattern:

```gitignore
target/*
!target/manifest.json
```

If the dbt project lives in a subfolder, scope the exception to that folder:

```gitignore
<project.root>/target/*
!<project.root>/target/manifest.json
```

## Agent Responsibilities vs User

| Step | Agent does | User does |
|---|---|---|
| Generate dbt metadata | Run `dbt docs generate` or `dbt parse` | Review results |
| Commit manifest | Commit only `target/manifest.json` when Agents Schema is enabled | Approve commit |
| Create workflow file | Yes | Approve commit/push |
| Add `WAREHOUSE_CREDENTIALS` | No | Add in GitHub UI |
| Run workflow | Can trigger or instruct | Approve when needed |
| Verify `AGENTS.*` tables | Query/check after sync | Provide access if blocked |

## Validation

1. Run the workflow manually with `workflow_dispatch`.
2. Confirm the `AGENTS` schema exists.
3. Confirm dbt metadata tables exist.
4. Test an agent metadata query.

Example checks:

```sql
select *
from AGENTS.ROOT;
```

```sql
select *
from AGENTS.DBT_MODEL;
```

## Commit Separately

```powershell
git add .github/workflows/agents-schema-dbt.yml <project.root>/target/manifest.json
git commit -m "Add Agents Schema sync workflow"
```

Ask user before commit. Do not mix this commit with model-layer commits.
