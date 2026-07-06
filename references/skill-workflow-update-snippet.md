# Skill Workflow Update Snippet

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

## Final Acceptance Gate

Before final delivery, the agent must run:

```bash
python scripts/run_acceptance_gate.py --root .
```

The final answer must not claim project completion if this script returns FAIL.

The generated project should include:

```text
reports/agent/ACCEPTANCE_GATE_REPORT.md
reports/agent/ACCEPTANCE_GATE_REPORT.json
```
