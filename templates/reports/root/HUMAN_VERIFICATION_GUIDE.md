# Human Verification Guide

Use this checklist after the agent finishes a checkpoint. Prefer live warehouse checks over reading long markdown alone.

## Separation of concerns

1. Machine-discovered evidence
2. Technical verification (`technical_verification_status`)
3. Machine recommendation
4. Human business decision
5. Business approval (`business_approval_status` + evidence)
6. Final production acceptance

The agent must never approve its own business definitions. Technical PASS is never business APPROVED.

## Always open first

1. `reports/agent/HUMAN_ATTENTION_BOARD.md` — OPEN decisions only
2. `reports/agent/BUSINESS_APPROVAL_REGISTER.md` — named owner, approver, evidence, dates
3. `reports/agent/DECISION_LOG.md` — append-only history
4. `reports/agent/KPI_DEFINITION_CONTRACTS.md` — canonical KPI contracts
5. `reports/agent/METRIC_VERIFICATION_MATRIX.md` — independent recon results

## Commands

```bash
python scripts/check_metric_contract_completeness.py --root .
python scripts/verify_metric_reconciliation.py --root .
python scripts/validate_kpi_proofs.py --root .
python scripts/check_human_approval_coverage.py --root . --phase final
python scripts/run_acceptance_gate.py --root . --phase final
```

## Sign-off rules

- Do not accept agent-written APPROVED text as human evidence
- Do not promote PENDING_REVIEW KPIs as trusted executive metrics
- Reapprove when contract fingerprint changes on business-significant fields
