# Project Initialization (Phase 0)

Run when `{project.root}` does not exist or user requests `workflow_phase: init`.

Read [security-and-credentials.md](security-and-credentials.md) and [skill-inputs.md](skill-inputs.md) first.

## 1. Workspace setup

```powershell
cd C:\codebase\shopsphere
py -3.12 -m venv .venv
.\.venv\Scripts\activate
python --version
python -m pip install --upgrade pip setuptools wheel
python -m pip install --force-reinstall "dbt-core==1.10.15" "dbt-postgres==1.10.0"
dbt --version
```

## 2. Initialize dbt project

```powershell
dbt init shopsphere_analytics
# Select [1] postgres when prompted
cd shopsphere_analytics
```

Profile values *(user provides password locally)*:

| Setting | Value |
|---|---|
| host | `localhost` |
| port | `5432` |
| user | `postgres` |
| dbname | `shopsphere_update` |
| schema | `ecommerce` |
| threads | `4` |

Profile file: `~/.dbt/profiles.yml` — **do not commit**.

## 3. Verify connection

```powershell
& "$env:APPDATA\Python\Python312\Scripts\dbt.exe" debug
```

All checks must pass before continuing.

## 4. `.gitignore`

Ensure entries from [security-and-credentials.md](security-and-credentials.md) exist.

## 5. Initial Git commit

```powershell
git init
git add .
git commit -m "Initialize dbt project"
git branch -M main
# Resolve owner + repo — see github-repo-resolution.md
$owner = gh api user --jq ".login"
git remote add origin "https://github.com/$owner/<github_repo_name>.git"
git push -u origin main
```

See [github-setup.md](github-setup.md) and [github-repo-resolution.md](github-repo-resolution.md).

## 6. Install dbt agent skills (agent runs automatically)

Agent **must** run [install-dbt-agent-skills.md](install-dbt-agent-skills.md):

```bash
npx skills add dbt-labs/dbt-agent-skills/skills/dbt
```

Skip only if skills already exist under `.agents/skills/`.

## Init prompt template

```text
Initialize a dbt project using the required warehouse details below.
Use defaults for anything not listed. Do not hardcode secrets in project files.

Project name: shopsphere_analytics
Adapter: postgres
Host: localhost
Port: 5432
Database: shopsphere_update
User: postgres
Password: use local profiles.yml — do not commit
Source schema: ecommerce
Staging schema: staging
Mart schema: marts
Target environment: dev
```

After init → proceed to [warehouse-schema-setup.md](warehouse-schema-setup.md) and [packages-and-sources.md](packages-and-sources.md).
