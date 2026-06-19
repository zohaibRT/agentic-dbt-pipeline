# GitHub Setup

Initial repository setup. Layer-by-layer commits: [git-workflow.md](git-workflow.md).
Repo resolution: [github-repo-resolution.md](github-repo-resolution.md).

## Prompt requirement

```text
github_repo_name: analytics    # repo slug only - owner from gh CLI
```

Agent resolves owner via `gh api user --jq ".login"` - **never hardcode accounts**.

## First-time setup

Create `.gitignore` before the first commit and confirm it excludes secrets and generated dbt artifacts.

```powershell
$owner = gh api user --jq ".login"
$repo = "<github_repo_name from user>"
git init
git status
git add .
git commit -m "Initialize dbt project"
git branch -M main
git remote add origin "https://github.com/$owner/$repo.git"
# Push only after approval.
# git push -u origin main
```

If repo does not exist: `gh repo create $repo --private --source=. --remote=origin --push` *(ask user first)*.

## Staged commit order (full project lifecycle)

| Stage | Stage paths | Commit message |
|---|---|---|
| 1. Init | project skeleton + safe `.gitignore` only | `Initialize dbt project` |
| 2. Packages | `packages.yml` | `Add dbt packages` |
| 3. Lock file | `package-lock.yml` | `Install dbt packages` |
| 4. Safe config/profile examples | `dbt_project.yml`, `.env.example`, `profiles.example.yml` | `Configure dbt profile and source settings` |
| 5. Evaluator config | `dbt_project.yml` dispatch | `Configure dbt project evaluator` |
| 6. Sources | `models/sources/` | `Define dbt sources` |
| 7. Layer 1 | `models/{layer_1_name}/{domain}/` | `Add dbt staging layer for {source} sources.` |
| 8. Layer 2 | `models/{layer_2_name}/{domain}/` | `Add dbt intermediate layer for {source} analytics.` |
| 9. Layer 3 | `models/{layer_3_name}/{domain}/` | `Add dbt marts layer for {source} star schema.` |
| 10. Semantic layer | `models/semantic/` or `*_semantic.yml` | `Add semantic layer metrics` |
| 11. Docs/tests | model YAML updates | `Add dbt tests and documentation` |
| 12. CI | `.github/workflows/` | `Add dbt automation workflows` |
| 13. Agents Schema | `agents-schema-dbt.yml` | `Add Agents Schema sync workflow` |

Do not start package, source, staging, intermediate, mart, docs, CI, or Agents Schema changes until the initial commit exists.

## Before every commit

```powershell
git status
$dbt = "dbt"
& $dbt parse --no-partial-parse
```

## Never commit

`.venv/`, `target/`, `logs/`, `dbt_packages/`, `.env`, `profiles.yml`

Agents Schema exception: commit only `<project.root>/target/manifest.json` when the Agents Schema workflow needs it.
