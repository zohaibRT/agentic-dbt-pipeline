# Software Prerequisites

Use this before discovery commands that need a warehouse profile adapter, before project setup, and again before presentation or CI work.

The agent must detect missing software, install what it can safely install, and stop with `BLOCKED` when a required tool needs manual user action.

Also read [bootstrap.md](bootstrap.md), [project-initialization.md](project-initialization.md), [env-configuration.md](env-configuration.md), and [matplotlib-presentation-layer.md](matplotlib-presentation-layer.md).

## Goal

Support the complete pipeline by making every required tool explicit:

```text
detect -> install when safe -> verify -> document in setup report
```

Do not assume dbt, Python packages, git, or Node tools are already present.

## Software stack by phase

| Phase | Required software | Optional / later |
|---|---|---|
| First run / `.env` | Python 3.10+ | - |
| Discovery | Python, dbt profile in `~/.dbt/profiles.yml`, warehouse network access | dbt CLI if discovery uses dbt show/debug |
| Project setup | Python, pip/venv, dbt-core, dbt adapter, git, skill `requirements.txt` packages | `gh` when GitHub push/CI is requested |
| Sources / layers | dbt CLI, dbt packages via `dbt deps` | - |
| Analytics | dbt CLI, PyYAML | - |
| Matplotlib presentation | matplotlib, numpy, pandas, warehouse Python client if querying from Python | browser for local report review |
| Power BI presentation | Power BI Desktop when Desktop validation is expected | Power BI Modeling MCP / `pbi-cli` only when approved |
| CI / GitHub automation | git, `gh` | GitHub Actions runner (cloud) |
| Independent verification | Python, dbt CLI when warehouse checks are required | - |

## Required core tools

### 1. Python

| Item | Requirement |
|---|---|
| Version | Python 3.10+ (prefer 3.12) |
| Why | Skill scripts, report skeleton, acceptance gates, Matplotlib |
| Detect | `python --version` or `py -3.12 --version` |
| Install | User installs Python if missing; agent cannot invent a system Python |
| Block if missing | Yes for setup and later phases |

### 2. Virtual environment

| Item | Requirement |
|---|---|
| Tool | `venv` |
| Why | Isolate dbt and Python packages from system Python |
| Detect | `.venv/` exists or can be created |
| Install | `py -3.12 -m venv .venv` then activate |
| Block if missing | Yes when dbt/Python packages must be installed |

### 3. pip / setuptools / wheel

| Item | Requirement |
|---|---|
| Why | Install skill and dbt packages |
| Detect | `python -m pip --version` |
| Install | `python -m pip install --upgrade pip setuptools wheel` |
| Block if missing | Yes for setup |

### 4. dbt Core

| Item | Requirement |
|---|---|
| Version | Pin to supported version used by the skill (default `dbt-core==1.10.15`) |
| Why | Parse/build/test models |
| Detect | `dbt --version` |
| Install | `python -m pip install "dbt-core==1.10.15"` |
| Block if missing | Yes before sources/layer builds |

### 5. dbt adapter package

Install only the adapter that matches the selected profile:

| Profile `type` | Package |
|---|---|
| postgres | `dbt-postgres` |
| redshift | `dbt-redshift` |
| snowflake | `dbt-snowflake` |
| bigquery | `dbt-bigquery` |
| databricks | `dbt-databricks` |

Do not install every adapter by default.

### 6. Skill Python utilities

From skill/workspace `requirements.txt`:

- `PyYAML`
- `matplotlib`
- `numpy`
- `pandas`

Install with:

```powershell
python -m pip install -r <path-to-installed-skill-or-workspace>\requirements.txt
```

### 7. Git

| Item | Requirement |
|---|---|
| Why | Local commits, phase history, PR workflow |
| Detect | `git --version` |
| Install | User installs Git for Windows / system git if missing |
| Block if missing | WARN for local-only work; BLOCKED when commits/push are required |

### 8. Node.js / npx

| Item | Requirement |
|---|---|
| Why | `npx skills add` for this skill and dbt Agent Skills |
| Detect | `node --version`, `npx --version` |
| Install | User installs Node.js LTS if missing |
| Block if missing | BLOCKED only when skill hydration/install is still needed |

### 9. GitHub CLI (`gh`)

| Item | Requirement |
|---|---|
| Why | Repo resolution, authenticated push, PR creation |
| Detect | `gh --version` |
| Install | User installs GitHub CLI if missing |
| Block if missing | Only when push/CI/GitHub automation is requested |

### 10. dbt packages (inside project)

Managed by `packages.yml` + `dbt deps`, not system installers:

- codegen
- dbt_utils
- dbt_expectations
- dbt_project_evaluator
- audit_helper

### 11. Presentation extras

| Tool | When required |
|---|---|
| matplotlib / numpy / pandas | Matplotlib presentation approved |
| Warehouse Python client | Python queries against warehouse for charts |
| Power BI Desktop | Power BI Desktop validation expected |
| Browser | Manual review of local web report |

### 12. Profiles and credentials

| Item | Requirement |
|---|---|
| `~/.dbt/profiles.yml` | Required for warehouse connection |
| Workspace `.env` | Required non-secret inputs |
| Secrets | Never committed; never hardcoded |

## Detection and install order

During project setup, run this sequence:

```text
1. Python available?
2. Create/activate .venv
3. Upgrade pip/setuptools/wheel
4. Install skill requirements.txt
5. Resolve selected dbt profile adapter
6. Install dbt-core + matching adapter
7. Verify dbt --version
8. Verify git (and gh if GitHub requested)
9. Run dbt debug
10. Write software prerequisite results into setup_report.md
```

Use the checker:

```powershell
python <path-to-installed-skill-or-workspace>\scripts\check_software_prerequisites.py --root <project-or-workspace-root>
```

Optional flags:

```powershell
python ...\scripts\check_software_prerequisites.py --root . --require-git --require-gh --adapter postgres
```

## Agent behavior

| Situation | Action |
|---|---|
| Python missing | `BLOCKED`; ask user to install Python 3.12 |
| venv/pip missing | Create/repair if possible; otherwise `BLOCKED` |
| dbt missing | Install into active venv automatically during setup |
| Adapter missing | Install matching adapter only |
| skill requirements missing | Install from `requirements.txt` |
| git missing | `WARN` unless commit/push required |
| `gh` missing | `WARN`/`BLOCKED` only if GitHub work requested |
| Node/npx missing | `BLOCKED` only if skill install/hydration still needed |
| Power BI Desktop missing | `WARN`/`BLOCKED` only for Power BI Desktop validation |
| Network/permission install failure | Document commands attempted; mark `BLOCKED` |

## Required setup report section

`reports/agent/01_setup/setup_report.md` must include:

```markdown
## Software Prerequisites

| Software | Required for | Detected | Installed / action | Status | Notes |
|---|---|---|---|---|---|
| Python | scripts + dbt env | <version or missing> | <action> | PASS/WARN/FAIL/BLOCKED | <notes> |
| venv | isolated installs | <yes/no> | <action> | ... | ... |
| pip | package install | <version or missing> | <action> | ... | ... |
| dbt-core | build/test | <version or missing> | <action> | ... | ... |
| dbt adapter | warehouse | <adapter/version or missing> | <action> | ... | ... |
| Skill requirements.txt | YAML/scripts/presentation | <ok/missing> | <action> | ... | ... |
| git | commits | <version or missing> | <action> | ... | ... |
| Node/npx | skill install | <version or missing> | <action> | ... | ... |
| gh | GitHub automation | <version or missing/n/a> | <action> | ... | ... |
```

## Do not

- Install every warehouse adapter “just in case”
- Put passwords into install commands or reports
- Skip documenting a missing required tool
- Claim setup PASS when dbt is missing and layer work is next
- Ask the user to manually install packages the agent can safely install into `.venv`

## Completion rule

Setup may continue only when:

- Python + venv + pip are available
- dbt-core and the selected adapter are installed and verified
- skill utility requirements are installed or the skip is documented
- missing optional tools are marked WARN/N/A with reason

If a required tool cannot be installed, mark setup `BLOCKED` and ask the user.
