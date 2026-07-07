# CI/CD - GitHub Actions

Basic dbt validation on pull requests; Agents Schema sync on `main`.

Before creating or changing workflow files, follow [phase-plan-approval.md](phase-plan-approval.md).

## Acceptance gate workflow

This skill repo ships [.github/workflows/dbt_acceptance_gate.yml](../.github/workflows/dbt_acceptance_gate.yml).

- In the **skill repository**, the workflow validates skill configuration and compiles Python scripts on every pull request.
- In a **generated dbt project**, copy or adapt the commented `dbt-project-acceptance` job when warehouse CI credentials are available.

Generated projects should run at minimum:

```bash
dbt deps
dbt parse --no-partial-parse
dbt build
python scripts/run_acceptance_gate.py --root .
```

When analytics KPI catalogs exist:

```bash
python scripts/validate_kpi_proofs.py --root .
python scripts/check_requirement_traceability.py --root .
python scripts/check_layer_proof_coverage.py --root .
python scripts/verify_metric_reconciliation.py --root .
```

Upload `reports/agent/ACCEPTANCE_GATE_REPORT.md`, `ACCEPTANCE_GATE_REPORT.json`, and independent verification reports as CI artifacts when available.

See [independent-verification-governance.md](independent-verification-governance.md).

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
      # - run: dbt build --select +path:models/<layer_1_name>/<project_slug>
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

## State-based continuous integration

When prior production artifacts are available, prefer state-based selectors for pull request checks:

```powershell
dbt build --select state:modified+ --defer --state path/to/artifacts
```

Use this pattern to reduce cost and validate only changed models plus downstream dependencies. Fall back to path-based scoped builds when state artifacts are not available.

For GitHub Actions, persist or download the latest `manifest.json` and related artifacts from the main branch before running state-based validation. If artifact retrieval is not configured, document that state-based continuous integration is not ready yet and keep the workflow on `dbt parse` plus scoped build.
