# CI/CD - GitHub Actions

Basic dbt validation on pull requests; Agents Schema sync on `main`.

Before creating or changing workflow files, follow [phase-plan-approval.md](phase-plan-approval.md).

## PR validation workflow

Create `.github/workflows/dbt-ci.yml`:

```yaml
name: dbt CI

on:
  pull_request:
    branches: [main]
    paths:
      - '<project.root>/**'

jobs:
  dbt-validate:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: <project.root>
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install "dbt-core==1.10.15" "<dbt-adapter-package-for-selected-profile>"
      - run: dbt deps
      - run: dbt parse --no-partial-parse
      # Uncomment when CI warehouse credentials are configured:
      # - run: dbt build --select +path:models/<layer_1_name>/<domain>
      env:
        DBT_PROFILES_DIR: ${{ github.workspace }}/.dbt-ci
```

Use GitHub Secrets for CI warehouse credentials - never commit profiles.

Replace `<dbt-adapter-package-for-selected-profile>` only after the dbt profile adapter is known. Examples: `dbt-postgres`, `dbt-redshift`, `dbt-snowflake`, `dbt-bigquery`, or `dbt-databricks`.

## Production deployment

- Keep **PR validation** separate from **production deploy**
- Agents Schema sync on push to `main` - see [agents-schema-setup.md](agents-schema-setup.md)

## Commit

```powershell
git add .github/workflows/
git commit -m "Add dbt automation workflows"
```

Ask user before commit.

## Required CI steps (when warehouse available)

1. `dbt deps`
2. `dbt parse`
3. `dbt build` *(scoped selector - not full project unless approved)*
