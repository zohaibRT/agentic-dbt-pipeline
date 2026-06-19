# GitHub Repo Resolution (via GitHub CLI)

**Never hardcode a GitHub account** in prompts, `project.config.yml`, or skill examples.

## Agent workflow

1. **Detect logged-in account** (required before git init/push):

```powershell
gh auth status
$owner = gh api user --jq ".login"
```

If `gh` is not authenticated -> ask user to run `gh auth login`, then retry.

2. **Ask user only for the repository name** (slug), not the full URL:

```text
Which GitHub repository name should I use? (e.g. analytics, hospital-analytics, finance-dbt)
Owner will be: {owner from gh}
```

3. **Build remote URL**:

```text
https://github.com/{owner}/{github_repo_name}.git
```

4. **Configure git**:

```powershell
git remote add origin "https://github.com/$owner/$repo.git"   # if origin missing
git branch -M main
git push -u origin main
```

## Prompt field

```text
github_repo_name: analytics    # user provides repo slug only
push_to_github: true
commit: ask
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
