---
wo: WO-112
title: Frontmatter Generators
status: Complete
phase: 35
phase_name: Machine-Readable WO Contracts
wo_class: harness
write_scope:
  - docs/planning/WO-112-frontmatter-generators.md
  - docs/planning/WO-INDEX.md
  - docs/evidence/vnext/generated-inventory.json
  - plugins/vibeos/scripts/wo-contracts.py
  - tests/test_wo_contracts.py
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

# WO-112: Frontmatter Generators

## Status

`Complete`

## Phase

Phase 35: Machine-Readable WO Contracts

## Objective

Generate deterministic scope, agent-policy, and auditor-requirement artifacts from one Work Order frontmatter contract.

## Scope

### In Scope
- [x] Add a standalone `wo-contracts.py` CLI that parses WO frontmatter
- [x] Emit a worktree-scope manifest entry compatible with `plugins/vibeos/reference/worktree-scopes.schema.json`
- [x] Emit deterministic agent allow/deny policy material from `write_scope`, `no_touch`, `model_policy`, and `budget_posture`
- [x] Emit an auditor-requirement key for later Phase 42 auditor-artifact gates
- [x] Add tests proving deterministic output and known-bad failure behavior

### Out of Scope
- Backfilling historical Work Orders
- Registering a blocking frontmatter lint gate
- Changing `worktree-scopes.schema.json`
- Implementing the Phase 42 auditor-artifact gate

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-111 | Frontmatter schema and templates | Complete |

## Impact Analysis

- **Files created:** `plugins/vibeos/scripts/wo-contracts.py`, `tests/test_wo_contracts.py`, this WO
- **Files modified:** `docs/planning/WO-INDEX.md`, `docs/evidence/vnext/generated-inventory.json`
- **Systems affected:** Phase 35 machine-readable WO contract tooling

## Acceptance Criteria

- [x] AC-1: `wo-contracts.py` parses WO YAML frontmatter without requiring optional third-party packages
- [x] AC-2: `emit-worktree-scope` emits schema-compatible `branches`/`shared_paths` JSON for a supplied `feat/*` branch
- [x] AC-3: `emit-agent-policy` produces stable allow/deny material from `write_scope` and `no_touch`
- [x] AC-4: `emit-auditor-requirements` produces a stable key containing `wo`, `wo_class`, `required_auditors`, and governance defaults when available
- [x] AC-5: Tests cover successful output, deterministic repeat output, invalid branch failure, and missing frontmatter failure

## Test Strategy

- **Unit tests:** `python3 -m pytest tests/test_wo_contracts.py`
- **Compile:** `python3 -m py_compile plugins/vibeos/scripts/wo-contracts.py tests/test_wo_contracts.py`
- **Full suite:** `python3 -m pytest tests`
- **Gate proof:** `bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos`

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: WO-112 is a deterministic generator slice only. It deliberately does not widen the existing `feat/*` worktree-scope schema.
- Test status: Pending at implementation start.

### Pre-Implementation Audit
- Status: `complete`
- Findings: The generator should use the WO-111 schema artifact for class governance defaults, but full JSON Schema validation remains out of scope until WO-113 lint.
- Test status: Pending at implementation start.

### Pre-Commit Audit
- Status: `complete`
- Findings: The generator emits deterministic JSON from WO frontmatter and does not claim runtime enforcement. Worktree-scope output remains bound to the existing `feat/*` schema contract.
- Test status: Focused generator tests passed; real WO-112 generator trace passed; full suite passed; `pre_commit` gate passed.

## Evidence

- [x] Implementation complete
- [x] Tests pass
- [x] Gates pass
- [x] Documentation updated

### Proof Commands

```bash
python3 -m py_compile plugins/vibeos/scripts/wo-contracts.py tests/test_wo_contracts.py

python3 -m pytest tests/test_wo_contracts.py
# 6 passed in 0.35s

python3 plugins/vibeos/scripts/wo-contracts.py parse --wo-file docs/planning/WO-112-frontmatter-generators.md
python3 plugins/vibeos/scripts/wo-contracts.py emit-worktree-scope --wo-file docs/planning/WO-112-frontmatter-generators.md --branch feat/wo-112-frontmatter-generators
python3 plugins/vibeos/scripts/wo-contracts.py emit-agent-policy --wo-file docs/planning/WO-112-frontmatter-generators.md
python3 plugins/vibeos/scripts/wo-contracts.py emit-auditor-requirements --wo-file docs/planning/WO-112-frontmatter-generators.md
# All four real WO-112 generator commands exited 0 and emitted deterministic JSON artifacts.

python3 -m pytest tests
# 147 passed in 33.62s

bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos
# Total: 10 | Passed: 6 | Failed: 0 | Skipped: 4
# Result: PASS

python3 plugins/vibeos/scripts/generate-inventory.py --project-dir .
# PASS: wrote docs/evidence/vnext/generated-inventory.json
```
