# Agent Instructions

This repository contains a dbt analytics engineering agent workflow. Use `SKILL.md` as the main workflow controller and load the relevant reference files before changing dbt project files.

## Default Workflow

1. Discovery and requirements
2. Discovery approval checklist and requirements traceability matrix
3. Project setup and configuration
4. Sources
5. Staging
6. Intermediate
7. Marts
8. Validation
9. Documentation
10. Analytics insight reporting
11. Presentation layer (optional after approval)
12. Acceptance gate script
13. Independent verifier agent (fresh context, reads repo only)
14. Human sign-off

Semantic layer, project evaluator, analytics insight reporting, presentation layer, continuous integration, Agents Schema, commits, and pushes require the approval rules in `SKILL.md`.

## Independent verification

Verification must not depend only on the builder agent or the same chat window.

- Builder agent writes evidence to `reports/agent/`, SQL proofs, and dbt artifacts.
- Run `python scripts/run_acceptance_gate.py --root .` before final delivery.
- Run `python scripts/check_requirement_traceability.py --root .`, `python scripts/check_layer_proof_coverage.py --root .`, and `python scripts/verify_metric_reconciliation.py --root .` before final delivery.
- Run a fresh verifier agent with `agents/dbt-verifier-agent.md` for an independent audit report.
- Use `.github/workflows/dbt_acceptance_gate.yml` in generated projects when CI is enabled.

See `references/independent-verification-governance.md`.

## Before Editing

- Read `project.config.yml`.
- Identify the current workflow phase.
- Read the matching reference file in `references/`.
- Explain the plan before non-setup build changes.
- Keep changes limited to the approved phase.

Creating or updating workspace `.env` from user-provided values on first run is allowed per `references/env-configuration.md`. Do not commit `.env`.

## Safety Rules

Do not:

- Edit `target/`, `dbt_packages/`, `logs/`, `.venv/`, or `profiles.yml`.
- Commit workspace `.env`, secrets, passwords, tokens, or warehouse credentials.
- Tell users to create workspace `.env` manually before the first prompt when the skill can create it on first run per `references/env-configuration.md`.
- Run discovery or dbt commands while workspace `.env` is missing or placeholder-only.
- Hardcode credentials in SQL, YAML, Markdown, workflows, or scripts.
- Update, insert, delete, truncate, merge into, create, drop, alter, or repair rows or objects in the configured source schema or source tables.
- Write dbt outputs into the configured source schema.
- Create marts before staging and intermediate models are built and validated.
- Guess business metrics, mappings, relationships, reporting needs, or sensitive-field handling.
- Mark work complete when dbt tests or warehouse validation failed without documenting the blocker.
- Mark work complete when `scripts/run_acceptance_gate.py` returns `FAIL` or independent verification returns `FAIL`.

## Validation

After dbt model or YAML changes, run the smallest useful validation first, then broaden only as needed:

- `dbt parse --no-partial-parse`
- `dbt build --select <model_name>+`
- `dbt build --select +path:<layer_path>`
- `dbt test --select <model_name>`
- `python scripts/run_acceptance_gate.py --root .`
- `python scripts/validate_kpi_proofs.py --root .`
- `python scripts/check_requirement_traceability.py --root .`
- `python scripts/check_layer_proof_coverage.py --root .`
- `python scripts/verify_metric_reconciliation.py --root .`

Document validation commands, failures, fixes, skips, and remaining risks in the phase report.
