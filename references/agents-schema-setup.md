# Agents Schema Setup

Syncs dbt metadata to warehouse `AGENTS` schema for AI agent discovery.

## Prerequisites

- [ ] `dbt docs generate` produces `target/manifest.json`
- [ ] Destination warehouse supported by `dbt-labs/agents_schema`
- [ ] GitHub repository connected

## GitHub secret

Add secret: `WAREHOUSE_CREDENTIALS`

Store warehouse connection as YAML (not in repo):

```yaml
type: postgres
host: <database.host>
port: <database.port>
user: <warehouse_user>
password: <from-secret>
dbname: <database.dbname>
schema: <source.schema>
```

## Workflow file

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

Adjust `dbt-project-dir` to the folder containing `dbt_project.yml`.

## Agent responsibilities vs user (one-time only)

| Step | Agent does automatically | User does once |
|---|---|---|
| Install dbt-labs skills | ✅ `npx skills add ...` | — |
| `dbt deps` + codegen | ✅ | — |
| Build all layers | ✅ | — |
| Create `.github/workflows/*.yml` | ✅ | — |
| `profiles.yml` password | — | ✅ local only |
| GitHub `WAREHOUSE_CREDENTIALS` | — | ✅ GitHub UI |
| Approve git commit/push | asks | ✅ say yes/no |

## Validation

1. Run workflow manually (`workflow_dispatch`)
2. Confirm `AGENTS` schema exists in warehouse
3. Confirm metadata tables created
4. Test agent can query `AGENTS.*`

## Commit separately

```powershell
git add .github/workflows/agents-schema-dbt.yml
git commit -m "Add Agents Schema sync workflow"
```

Ask user before commit. Do not mix with model-layer commits.
