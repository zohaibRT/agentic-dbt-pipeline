# Project Initialization (Phase 0)

Run when `{project.root}` does not exist or user requests `workflow_phase: init`.

Read [security-and-credentials.md](security-and-credentials.md), [skill-inputs.md](skill-inputs.md), and [project-naming.md](project-naming.md) first.

Before running `dbt init`, resolve `dbt_project_name` and `dbt_project_root` from [project-naming.md](project-naming.md). Do not use `dbt_profile_name` as the project folder unless the user explicitly provided it as `dbt_project_name`.

## 1. Workspace setup

```powershell
cd <workspace_parent>
py -3.12 -m venv .venv
.\.venv\Scripts\activate
python --version
python -m pip install --upgrade pip setuptools wheel
python -m pip install --force-reinstall "dbt-core==1.10.15" "dbt-postgres==1.10.0"
dbt --version
```

## 2. Initialize dbt project

```powershell
dbt init <dbt_project_name>
# Select the adapter from database.adapter when prompted
cd <dbt_project_root>
```

After init, ensure `dbt_project.yml` has:

```yaml
name: <dbt_project_name>
profile: <dbt_profile_name>
```

Profile values *(user provides password locally)*:

| Setting | Value |
|---|---|
| host | `database.host` |
| port | `database.port` |
| user | from user or local profile |
| dbname | `database.dbname` |
| schema | `database.target_schema` |
| threads | `database.threads` |

Profile file: `~/.dbt/profiles.yml` - **do not commit**.

If more than one dbt profile exists, ask for `dbt_profile_name` and use that exact key as the dbt profile. Do not guess from the first profile in the file.

## 3. Verify connection

```powershell
dbt debug
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
# If github_repo_name is not local-only, resolve owner + repo after approval.
$owner = gh api user --jq ".login"
git remote add origin "https://github.com/$owner/<github_repo_name>.git"
# Push only after user approval.
# git push -u origin main
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

Project name: <dbt_project_name>
Project folder: <dbt_project_root>
dbt profile name: <dbt_profile_name>
Adapter: <database.adapter>
Host: <database.host>
Port: <database.port>
Database: <database.dbname>
User: <warehouse_user>
Password: use local profiles.yml - do not commit
Source schema: <source.schema>
Layer 1 schema suffix: <layer_names.layer_1>
Layer 3 schema suffix: <layer_names.layer_3>
Target environment: dev
```

After init -> proceed to [warehouse-schema-setup.md](warehouse-schema-setup.md) and [packages-and-sources.md](packages-and-sources.md).
