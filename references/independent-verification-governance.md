# Independent Verification Governance

Verification must **not** depend only on the same agent or the same chat window.

Use this enterprise design:

```text
Builder Agent
→ creates dbt project, reports, proofs, status files

Fresh Verifier Agent / MCP / CI
→ opens repo from zero context
→ reads only project files and dbt artifacts
→ runs dbt commands and validation scripts
→ produces independent audit report
```

Project memory lives in the repository, not the conversation.

## Roles

| Layer | Role |
|---|---|
| MCP | Access to repo, files, database, dbt commands, reports |
| Verifier Agent | Independent audit reasoning and report |
| Acceptance Script | Deterministic pass/fail gate |
| CI/CD | Enforcement on pull request and main |
| Human checklist | Final sign-off |

MCP is useful, but MCP itself is **not** the verifier.

## Required skill files

| File | Purpose |
|---|---|
| [agents/dbt-verifier-agent.md](../agents/dbt-verifier-agent.md) | Instructions for a fresh auditor agent |
| [scripts/run_acceptance_gate.py](../scripts/run_acceptance_gate.py) | Deterministic acceptance gate |
| [scripts/check_requirement_traceability.py](../scripts/check_requirement_traceability.py) | Requirement traceability gate |
| [scripts/check_layer_proof_coverage.py](../scripts/check_layer_proof_coverage.py) | Layer proof coverage gate |
| [scripts/verify_metric_reconciliation.py](../scripts/verify_metric_reconciliation.py) | Metric and key performance indicator reconciliation gate |
| [.github/workflows/dbt_acceptance_gate.yml](../.github/workflows/dbt_acceptance_gate.yml) | CI template for generated projects |
| [discovery-approval-checklist.md](discovery-approval-checklist.md) | Discovery approval standard |
| [requirements-traceability-matrix.md](requirements-traceability-matrix.md) | Requirement-to-artifact traceability |
| [layer-verification-ledger.md](layer-verification-ledger.md) | Per-model verification ledger |
| [kpi-definition-contract.md](kpi-definition-contract.md) | Key performance indicator contract standard |
| [metric-verification-checklist.md](metric-verification-checklist.md) | Metric verification matrix standard |
| [mcp/dbt-verifier-mcp.json](../mcp/dbt-verifier-mcp.json) | Optional MCP server wiring example |

## Discovery gate

After [discovery-requirements.md](discovery-requirements.md) completes, the builder agent must create:

```text
reports/agent/00_discovery/DISCOVERY_APPROVAL_CHECKLIST.md
reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md
reports/agent/KPI_DEFINITION_CONTRACTS.md
reports/agent/METRIC_VERIFICATION_MATRIX.md
```

Use:

- [discovery-approval-checklist.md](discovery-approval-checklist.md)
- [requirements-traceability-matrix.md](requirements-traceability-matrix.md)

Do not continue to bootstrap/build until the checklist decision is `APPROVED` or `APPROVED WITH CONDITIONS`.

If approved with conditions, write those conditions to:

```text
reports/agent/CONTEXT_TREE.md
AGENT_PLAN.md
reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md
```

## Layer verification gate

After every layer or phase, update:

```text
reports/agent/LAYER_VERIFICATION_LEDGER.md
reports/agent/PIPELINE_STATUS.md
reports/agent/CONTEXT_TREE.md
```

Use [layer-verification-ledger.md](layer-verification-ledger.md).

Every important model must have evidence for:

- row count
- grain/duplicate check
- null key check
- relationship/orphan check, where applicable
- measure/date sanity check, where applicable
- SQL proof file path
- PASS/WARN/FAIL/BLOCKED status

## Key performance indicator and metric verification gate

Before semantic layer, analytics insight reporting, presentation layer, or final delivery, maintain:

```text
reports/agent/KPI_DEFINITION_CONTRACTS.md
reports/agent/METRIC_VERIFICATION_MATRIX.md
```

Use:

- [kpi-definition-contract.md](kpi-definition-contract.md)
- [metric-verification-checklist.md](metric-verification-checklist.md)

Every approved or proposed key performance indicator must have business meaning, source mapping, formula, grain, date basis, included/excluded rows, proof file, expected result, actual result, difference or tolerance, approval status, and verification status.

Every important measure, metric, and key performance indicator must reconcile source proof to mart proof, and semantic/presentation proof when those layers exist.

## Final acceptance gate

Before final delivery, the builder agent must run:

```bash
python scripts/run_acceptance_gate.py --root .
python scripts/check_requirement_traceability.py --root .
python scripts/check_layer_proof_coverage.py --root .
python scripts/verify_metric_reconciliation.py --root .
```

Do not claim project completion if any hard gate returns `FAIL`.

Generated projects should include:

```text
reports/agent/ACCEPTANCE_GATE_REPORT.md
reports/agent/ACCEPTANCE_GATE_REPORT.json
```

## Independent verifier phase

After the builder agent finishes presentation work or explicitly stops before presentation, run a **fresh verifier agent** using [agents/dbt-verifier-agent.md](../agents/dbt-verifier-agent.md).

The verifier must:

1. Start with zero builder chat context.
2. Read only repository files, dbt artifacts, and database evidence.
3. Run required commands when credentials allow.
4. Write `reports/agent/INDEPENDENT_VERIFICATION_REPORT.md` and `.json`.

Final delivery is blocked when independent verification is `FAIL`.

## CI gate

For generated dbt projects with GitHub automation, copy or adapt [.github/workflows/dbt_acceptance_gate.yml](../.github/workflows/dbt_acceptance_gate.yml).

CI should run at minimum:

1. `dbt deps`
2. `dbt parse --no-partial-parse`
3. `dbt build` when warehouse credentials are configured
4. `python scripts/run_acceptance_gate.py --root .`

See [cicd-setup.md](cicd-setup.md).

## Human approval

Before closing delivery, ensure `reports/agent/HUMAN_VERIFICATION_GUIDE.md` exists and the data engineer can verify layers, KPIs, blocked items, and presentation artifacts without reading the builder chat.
