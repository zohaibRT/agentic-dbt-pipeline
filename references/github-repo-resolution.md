# GitHub Repo Resolution (Optional, via GitHub CLI)

**Never hardcode a GitHub account** in prompts, `project.config.yml`, or skill examples.

Default to local-only git work. Do not run `gh` or ask for a repo name unless the user requests a push, provides `github_repo_name` / `DBT_GITHUB_REPO_NAME`, sets `push_to_github: true`, or an existing remote must be verified.

## Agent workflow

1. **Decide whether GitHub is needed**

Treat missing repo settings as local-only. Treat these values as local-only, not repository names:

```text
local-only, local, none, no, false, na, n/a, NA
```

When the resolved mode is local-only, skip `gh` remote setup and do not push.

2. **Detect logged-in account** (only when push/new remote is needed):

```powershell
gh auth status
$owner = gh api user --jq ".login"
```

If `gh` is not authenticated -> ask user to run `gh auth login`, then retry.

3. **Ask user only for the repository name** (slug), not the full URL, when no repo was provided:

```text
Which GitHub repository name should I use? (e.g. analytics, hospital-analytics, finance-dbt)
Owner will be: {owner from gh}
```

4. **Build remote URL**:

```text
https://github.com/{owner}/{github_repo_name}.git
```

5. **Configure git after approval**:

```powershell
git remote add origin "https://github.com/$owner/$repo.git"   # if origin missing
git branch -M main
# Push only after the user approves the push.
# git push -u origin main
```

## Prompt field

```text
github_repo_name: analytics    # optional; use only when pushing
```

Optional override (full URL or `other-owner/repo`) - only when user explicitly wants a different account:

```text
github_repo: other-owner/analytics
```

## Create repo if missing

If push fails with "repository not found", offer to create:

```powershell
gh repo create $repo --private --source=. --remote=origin --push
# or --public per user preference
```

Ask user before creating a new repository.

## Windows git note

If `git commit` fails with `unknown option trailer`, use:

```text
"C:\Program Files\Git\cmd\git.exe" commit -m "<message>"
```
