# GitHub Setup

Initial repository setup. Layer-by-layer commits: [git-workflow.md](git-workflow.md).  
Repo resolution: [github-repo-resolution.md](github-repo-resolution.md).

## Prompt requirement

```text
github_repo_name: analytics    # repo slug only — owner from gh CLI
push_to_github: true
commit: ask
```

Agent resolves owner via `gh api user --jq ".login"` — **never hardcode accounts**.

## First-time setup

```powershell
$owner = gh api user --jq ".login"
$repo = "<github_repo_name from user>"
git init
git add .
git commit -m "Initialize dbt project"
git branch -M main
git remote add origin "https://github.com/$owner/$repo.git"
git push -u origin main
```

If repo does not exist: `gh repo create $repo --private --source=. --remote=origin --push` *(ask user first)*.

## Staged commit order (full project lifecycle)

| Stage | Stage paths | Commit message |
|---|---|---|
| 1. Init | project skeleton | `Initialize dbt project` |
| 2. Packages | `packages.yml` | `Add dbt packages` |
| 3. Lock file | `package-lock.yml` | `Install dbt packages` |
| 4. Evaluator config | `dbt_project.yml` dispatch | `Configure dbt project evaluator` |
| 5. Sources | `models/sources/` | `Define dbt sources` |
| 6. Staging | `models/staging/{domain}/` | `Add dbt staging layer for ecommerce sources.` |
| 7. Intermediate | `models/intermediate/{domain}/` | `Add dbt intermediate layer for ecommerce analytics.` |
| 8. Marts | `models/marts/{domain}/` | `Add dbt marts layer for ecommerce star schema.` |
| 9. Semantic layer | `models/semantic/` or `*_semantic.yml` | `Add semantic layer metrics` |
| 10. Docs/tests | model YAML updates | `Add dbt tests and documentation` |
| 11. CI | `.github/workflows/` | `Add dbt automation workflows` |
| 12. Agents Schema | `agents-schema-dbt.yml` | `Add Agents Schema sync workflow` |

## Before every commit

```powershell
git status
& "$env:APPDATA\Python\Python312\Scripts\dbt.exe" parse --no-partial-parse
```

## Never commit

`.venv/`, `target/`, `logs/`, `dbt_packages/`, `.env`, `profiles.yml`
