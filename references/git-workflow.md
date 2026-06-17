# Git Workflow — Ask After Each Layer

## Default behavior

Resolve GitHub remote **before any git work** — [github-repo-resolution.md](github-repo-resolution.md):

1. `gh auth status` and `gh api user --jq ".login"` → `{owner}`
2. Read `github_repo_name` from prompt; **if missing, ask user** for repo slug only
3. Remote = `https://github.com/{owner}/{github_repo_name}.git`
4. Optional `github_repo:` override for a different owner/repo

**Never hardcode GitHub accounts** in skill files or `project.config.yml`.

After **each layer** completes successfully (`dbt parse` + `dbt build` PASS):

1. Summarize the layer results.
2. **Ask the user:**  
   `"{Layer name} is complete. Commit and push to https://github.com/{owner}/{github_repo_name}?"`
3. Wait for the answer before any git command.

| User answer | Action |
|---|---|
| **Yes** / **y** / **commit** | Stage layer files → commit → push to `github_repo` if `push_to_github: true` |
| **No** / **n** / **skip** | Do not commit; proceed to next layer or finish |

Use the **AskQuestion** tool when available. Otherwise ask in chat and wait.

## Never do this

- Commit without asking (unless user set `commit: auto_yes` in the prompt)
- Push without user saying yes to that layer
- Stage `.venv`, `target/`, `logs/`, `dbt_packages/`, `.env`, `profiles.yml`
- Commit unrelated layers in one commit

## Pre-commit validation (re-run if build was a while ago)

From `{project.root}`:

```powershell
& "$env:APPDATA\Python\Python312\Scripts\dbt.exe" parse --no-partial-parse
& "$env:APPDATA\Python\Python312\Scripts\dbt.exe" build --select +path:<layer_path>
```

Examples:

```powershell
& "$env:APPDATA\Python\Python312\Scripts\dbt.exe" build --select +path:models/staging/ecommerce
& "$env:APPDATA\Python\Python312\Scripts\dbt.exe" build --select +path:models/intermediate/ecommerce
& "$env:APPDATA\Python\Python312\Scripts\dbt.exe" build --select +path:models/marts/ecommerce
```

## Stage only this layer (use user-defined folder names)

| Role | Stage paths |
|---|---|
| Sources | `models/sources/` |
| Layer 1 | `models/{layer_1_name}/{domain}/` |
| Layer 2 | `models/{layer_2_name}/{domain}/` |
| Layer 3 | `models/{layer_3_name}/{domain}/` + `dbt_project.yml` if changed |

Run from `{project.root}` (where `.git` lives).

## Full staged commit sequence

See [github-setup.md](github-setup.md) for init → packages → sources → layers → docs → CI.

## Commit messages (use layer role, not user name)

| Stage | Message |
|---|---|
| Init | `Initialize dbt project` |
| Packages | `Add dbt packages` |
| Lock file | `Install dbt packages` |
| Config | `Configure dbt profile and source settings` |
| Sources | `Define dbt sources` / `Generate {source} source YAML` |
| Layer 1 | `Add dbt staging layer for {source} sources.` |
| Layer 2 | `Add dbt intermediate layer for {source} analytics.` |
| Layer 3 | `Add dbt marts layer for {source} star schema.` |
| Docs | `Add dbt tests and documentation` |
| CI | `Add dbt automation workflows` |
| Agents Schema | `Add Agents Schema sync workflow` |

## Push

After commit, push to `github_repo` when user approved and `push_to_github` is not `false`:

```powershell
git remote add origin <github_repo>   # if origin missing
git branch -M main
git push -u origin main
```

For per-layer pushes after the first: `git push origin main`

Report: commit hash, files committed, remote URL (`github_repo`).

## Windows git note

If `git commit` fails with `unknown option trailer`, use:

```text
"C:\Program Files\Git\cmd\git.exe" commit -m "<message>"
```

## Prompt overrides

| `commit:` value | Behavior |
|---|---|
| `ask` *(default)* | Ask after each layer; push when user says yes and `push_to_github: true` |
| `auto_yes` | Commit and push each layer to `github_repo` without asking |
| `skip_all` | Never commit or push during this run |
