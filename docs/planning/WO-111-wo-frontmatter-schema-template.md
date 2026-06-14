---
wo: WO-111
title: WO Frontmatter Schema + Template
status: Complete
phase: 35
phase_name: Machine-Readable WO Contracts
wo_class: harness
write_scope:
  - docs/planning/WO-SCHEMA.md
  - docs/planning/WO-111-wo-frontmatter-schema-template.md
  - docs/planning/WO-TEMPLATE.md
  - docs/planning/DEVELOPMENT-PLAN.md
  - docs/planning/WO-INDEX.md
  - plugins/vibeos/reference/wo-frontmatter.schema.json
  - plugins/vibeos/reference/governance/WO-TEMPLATE.md.ref
  - tests/test_wo_frontmatter_schema.py
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

# WO-111: WO Frontmatter Schema + Template

## Status

`Complete`

## Phase

Phase 35: Machine-Readable WO Contracts

## Objective

Define the portable machine-readable Work Order frontmatter contract and update WO templates so later generators can derive scope, auditors, model policy, budget posture, and loop ceilings from one source of truth.

## Scope

### In Scope
- [x] Add JSON Schema for WO frontmatter
- [x] Document field semantics, class semantics, model-policy names, and generator handoffs
- [x] Update repo and reference WO templates with the frontmatter block
- [x] Add schema-focused tests with known-good and known-bad fixtures

### Out of Scope
- Building WO frontmatter generators
- Backfilling all historical WOs
- Making `WO-INDEX.md` generated
- Registering a blocking frontmatter lint gate

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| Phase 34 | Gate floor foundation | Complete |

## Acceptance Criteria

- [x] AC-1: `plugins/vibeos/reference/wo-frontmatter.schema.json` exists and is valid JSON
- [x] AC-2: `docs/planning/WO-SCHEMA.md` documents required fields and class governance semantics
- [x] AC-3: `docs/planning/WO-TEMPLATE.md` and `plugins/vibeos/reference/governance/WO-TEMPLATE.md.ref` include the contract block
- [x] AC-4: Tests cover known-good fixtures, missing required fields, invalid class values, custom extension classes, and invalid budget values

## Test Strategy

- **Unit tests:** `python3 -m pytest tests/test_wo_frontmatter_schema.py`
- **Schema parse:** `jq . plugins/vibeos/reference/wo-frontmatter.schema.json`
- **Gate proof:** `bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos`

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: WO-111 is schema/template only; generator behavior is explicitly reserved for WO-112 and migration for WO-113.
- Test status: Pending at implementation start.

### Pre-Implementation Audit
- Status: `complete`
- Findings: JSON Schema is the correct portable artifact because it can be consumed by Claude, Codex, and deterministic scripts without runtime-specific assumptions.
- Test status: Pending at implementation start.

### Pre-Commit Audit
- Status: `complete`
- Findings: Schema/template changes are docs and contract artifacts only. The schema is valid JSON, templates include all required contract fields, and the focused schema tests cover valid, invalid, and custom-extension cases.
- Test status: Focused schema test passed; full suite passed; `pre_commit` gate passed.

## Evidence

- [x] Implementation complete
- [x] Tests pass
- [x] Gates pass
- [x] Documentation updated

### Proof Commands

```bash
jq . plugins/vibeos/reference/wo-frontmatter.schema.json >/dev/null
python3 -m py_compile tests/test_wo_frontmatter_schema.py
python3 -m pytest tests/test_wo_frontmatter_schema.py
# 5 passed in 0.01s

python3 -m pytest tests
# 141 passed in 35.08s

bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos
# Total: 10 | Passed: 6 | Failed: 0 | Skipped: 4
# Result: PASS
```
