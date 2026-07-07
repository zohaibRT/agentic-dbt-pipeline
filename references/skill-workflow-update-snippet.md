# Skill Workflow Update Snippet

**Integrated into** [independent-verification-governance.md](independent-verification-governance.md) and `SKILL.md`. Keep this file as a short copy-paste aid.

Add these rules to the dbt skill workflow instructions.

## Discovery Gate

After `discovery-requirements.md` completes, the agent must create:

```text
reports/agent/00_discovery/DISCOVERY_APPROVAL_CHECKLIST.md
reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md
```

The agent must use:

```text
references/discovery-approval-checklist.md
references/requirements-traceability-matrix.md
```

The agent must not continue to bootstrap/build until the checklist decision is `APPROVED` or `APPROVED WITH CONDITIONS`.

If approved with conditions, those conditions must be written to:

```text
reports/agent/CONTEXT_TREE.md
AGENT_PLAN.md
reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md
```

## Layer Verification Gate

After every layer or phase, the agent must update:

```text
reports/agent/LAYER_VERIFICATION_LEDGER.md
reports/agent/PIPELINE_STATUS.md
reports/agent/CONTEXT_TREE.md
```

The agent must use:

```text
references/layer-verification-ledger.md
```

Every important model must have evidence for:

- row count
- grain/duplicate check
- null key check
- relationship/orphan check, where applicable
- measure/date sanity check, where applicable
- SQL proof file path
- PASS/WARN/FAIL/BLOCKED status

## KPI and Metric Verification Gate

Before semantic layer, analytics insight reporting, presentation layer, or final delivery, the agent must update:

```text
reports/agent/KPI_DEFINITION_CONTRACTS.md
reports/agent/METRIC_VERIFICATION_MATRIX.md
```

The agent must use:

```text
references/evidence-driven-dbt-process.md
references/kpi-definition-contract.md
references/metric-verification-checklist.md
```

Every key performance indicator must have business meaning, formula, grain, date basis, included and excluded rows, source mapping, expected result, actual result, difference or tolerance, SQL proof file, approval status, and verification status.

Every important measure, metric, and key performance indicator must reconcile source proof to mart proof, and semantic/presentation proof when those layers exist.

## Final Acceptance Gate

Before final delivery, the agent must run:

```bash
python scripts/run_acceptance_gate.py --root .
python scripts/check_requirement_traceability.py --root .
python scripts/check_layer_proof_coverage.py --root .
python scripts/verify_metric_reconciliation.py --root .
```

The final answer must not claim project completion if any hard gate returns FAIL.

The generated project should include:

```text
reports/agent/ACCEPTANCE_GATE_REPORT.md
reports/agent/ACCEPTANCE_GATE_REPORT.json
```

## Independent Verifier Phase

After builder work is complete, run a fresh verifier agent with `agents/dbt-verifier-agent.md` from zero context. Write:

```text
reports/agent/INDEPENDENT_VERIFICATION_REPORT.md
reports/agent/INDEPENDENT_VERIFICATION_REPORT.json
```

Do not claim final delivery if independent verification is FAIL.
