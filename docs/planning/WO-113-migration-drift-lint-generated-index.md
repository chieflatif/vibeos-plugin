---
wo: WO-113
title: Migration + Drift Lint + Generated WO-INDEX
status: Complete
phase: 35
phase_name: Machine-Readable WO Contracts
wo_class: harness
write_scope:
  - docs/planning/WO-106-vnext-generated-inventory-and-claim-ledger.md
  - docs/planning/WO-107-gate-runner-tier-schema-fix.md
  - docs/planning/WO-108-fixture-secret-quarantine-pytest-scoping.md
  - docs/planning/WO-109-runtime-capability-detection-repair.md
  - docs/planning/WO-110-hook-manifest-sync-status-reconciliation.md
  - docs/planning/WO-113-migration-drift-lint-generated-index.md
  - docs/planning/WO-145-phase34-gate-floor-remediation.md
  - docs/planning/WO-146-tests-pass-recursion-guard.md
  - docs/planning/WO-INDEX.md
  - docs/evidence/vnext/generated-inventory.json
  - plugins/vibeos/quality-gate-manifest.json
  - plugins/vibeos/scripts/validate-wo-frontmatter.sh
  - plugins/vibeos/scripts/wo-frontmatter-lint.py
  - tests/test_wo_frontmatter_lint.py
no_touch:
  - /Users/latifhorst/latifhorstweb/**
  - /Users/latifhorst/Joan4U/**
required_auditors:
  - correctness-auditor
  - evidence-auditor
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: null
  cost_ceiling_usd: null
---

# WO-113: Migration + Drift Lint + Generated WO-INDEX

## Status

`Complete`

## Phase

Phase 35: Machine-Readable WO Contracts

## Objective

Backfill the active vNext WO frontmatter set, generate the vNext index view from machine-readable sources, and add advisory drift linting.

## Scope

### In Scope
- [x] Backfill one historical fixture WO (`WO-106`) plus WO-107 and later implemented vNext WO files with frontmatter
- [x] Add a deterministic frontmatter lint/index generator
- [x] Generate the active/vNext block in `WO-INDEX.md` while preserving the legacy archive
- [x] Register `validate-wo-frontmatter.sh` in `wo_entry` as advisory
- [x] Add tests for required-frontmatter checks, scope/prose drift, generated-index idempotency, and hand-edit detection

### Out of Scope
- Backfilling every legacy pre-vNext WO
- Making the new lint gate blocking
- Implementing auditor-artifact completeness gates
- Creating placeholder WO files for every future planned WO

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-112 | Frontmatter generators | Complete |

## Acceptance Criteria

- [x] AC-1: WO-106 and all existing WO-107+ planning files carry valid frontmatter
- [x] AC-2: `validate-wo-frontmatter.sh` runs at `wo_entry` as an advisory gate
- [x] AC-3: The generated vNext block in `WO-INDEX.md` is reproducible and idempotent
- [x] AC-4: A deliberate edit to the generated index block fails validation in a fixture
- [x] AC-5: Frontmatter/prose scope drift fails validation in a fixture

## Test Strategy

- **Unit tests:** `python3 -m pytest tests/test_wo_frontmatter_lint.py`
- **Compile:** `python3 -m py_compile plugins/vibeos/scripts/wo-frontmatter-lint.py tests/test_wo_frontmatter_lint.py`
- **Real-path lint:** `bash plugins/vibeos/scripts/validate-wo-frontmatter.sh --project-dir .`
- **Gate proof:** `bash plugins/vibeos/scripts/gate-runner.sh wo_entry --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos`

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: Generated index scope is limited to the active/vNext machine-readable block so legacy historical context is preserved.
- Test status: Pending at implementation start.

### Pre-Implementation Audit
- Status: `complete`
- Findings: Lint should be advisory at first because the repo still contains many pre-vNext prose-only WOs. WO-106 is the historical fixture; WO-107+ is the active vNext migration floor.
- Test status: Pending at implementation start.

### Pre-Commit Audit
- Status: `complete`
- Findings: The vNext generated block is source-derived from frontmatter and the master plan, while legacy pre-vNext archive rows are preserved below it. The lint gate is registered as advisory at `wo_entry`, so it does not overclaim complete legacy backfill.
- Test status: Focused lint tests passed; real wrapper passed; `wo_entry` gate passed; full suite passed.

## Evidence

- [x] Implementation complete
- [x] Tests pass
- [x] Gates pass
- [x] Documentation updated

### Proof Commands

```bash
python3 -m py_compile plugins/vibeos/scripts/wo-frontmatter-lint.py tests/test_wo_frontmatter_lint.py

python3 -m pytest tests/test_wo_frontmatter_lint.py tests/test_status_reconciliation.py
# 10 passed in 0.57s

python3 plugins/vibeos/scripts/wo-frontmatter-lint.py lint --project-dir .
# PASS: frontmatter contracts are valid

python3 plugins/vibeos/scripts/wo-frontmatter-lint.py validate-index --project-dir .
# PASS: WO-INDEX.md generated block is current

bash plugins/vibeos/scripts/validate-wo-frontmatter.sh --project-dir .
# PASS: frontmatter contracts are valid
# PASS: WO-INDEX.md generated block is current

bash plugins/vibeos/scripts/gate-runner.sh wo_entry --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos
# Total: 3 | Passed: 1 | Failed: 0 | Skipped: 2
# Result: PASS

python3 -m pytest tests/test_status_reconciliation.py
# 4 passed in 0.24s

python3 -m pytest tests
# 153 passed in 36.57s

bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos
# Total: 10 | Passed: 6 | Failed: 0 | Skipped: 4
# Result: PASS
```
