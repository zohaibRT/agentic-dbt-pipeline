# Git Workflow - Ask After Each Layer

## Default behavior

Resolve GitHub remote **before any git work** - [github-repo-resolution.md](github-repo-resolution.md):

1. `gh auth status` and `gh api user --jq ".login"` -> `{owner}`
2. Read `github_repo_name` from prompt; **if missing, ask user** for repo slug only
3. Remote = `https://github.com/{owner}/{github_repo_name}.git`
4. Optional `github_repo:` override for a different owner/repo

**Never hardcode GitHub accounts** in skill files or `project.config.yml`.

Before any package, source, staging, intermediate, mart, docs, CI, or Agents Schema work, confirm the initial dbt project commit exists:

```powershell
git log --oneline -1
git status
```

If no commit exists, create only the initialized project skeleton plus safe `.gitignore`, then commit:

```powershell
git add .
git commit -m "Initialize dbt project"
```

After **each layer** completes successfully (`dbt parse` + `dbt build` PASS):

1. Summarize the layer results.
2. **Ask the user:**
   `"{Layer name} is complete. Commit and push to https://github.com/{owner}/{github_repo_name}?"`
3. Wait for the answer before any git command.

| User answer | Action |
|---|---|
| **Yes** / **y** / **commit** | Stage layer files -> commit -> push to `github_repo` if `push_to_github: true` |
| **No** / **n** / **skip** | Do not commit; proceed to next layer or finish |

Use the **AskQuestion** tool when available. Otherwise ask in chat and wait.

## Never do this

- Commit without asking (unless user set `commit: auto_yes` in the prompt)
- Push without user saying yes to that layer
- Stage `.venv`, `target/`, `logs/`, `dbt_packages/`, `.env`, `profiles.yml`
- Commit unrelated layers in one commit

Exception: when Agents Schema is enabled, commit only `<project.root>/target/manifest.json`; do not stage any other `target/` files.

## Pre-commit validation (re-run if build was a while ago)

From `{project.root}`:

```powershell
$dbt = "dbt"
& $dbt parse --no-partial-parse
& $dbt build --select +path:<layer_path>
```

Examples:

```powershell
& $dbt build --select +path:models/{layer_1_name}/{domain}
& $dbt build --select +path:models/{layer_2_name}/{domain}
& $dbt build --select +path:models/{layer_3_name}/{domain}
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

See [github-setup.md](github-setup.md) for init -> packages -> sources -> layers -> docs -> CI.

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
| `auto_yes` | Commit each layer without asking; push only when `push_to_github: true` and the target is not production |
| `skip_all` | Never commit or push during this run |
