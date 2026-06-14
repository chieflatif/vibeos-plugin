---
wo: WO-115
title: Lane-Readiness Gate
status: Complete
phase: 36
phase_name: Lane-Readiness Automation
wo_class: harness
write_scope:
  - docs/planning/WO-115-check-lane-readiness.md
  - docs/planning/WO-INDEX.md
  - docs/evidence/vnext/generated-inventory.json
  - plugins/vibeos/scripts/check-lane-readiness.sh
  - plugins/vibeos/scripts/lane-readiness.py
  - tests/test_lane_readiness.py
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

# WO-115: Lane-Readiness Gate

## Status

`Complete`

## Phase

Phase 36: Lane-Readiness Automation

## Objective

Add a deterministic lane-readiness command that validates a parallel lane by rebasing it in a scratch worktree, running `wo_exit`, validating its packet, and checking the actual diff against the WO `write_scope`.

## Scope

### In Scope
- [x] Add `plugins/vibeos/scripts/check-lane-readiness.sh`
- [x] Add testable lane-readiness implementation in `plugins/vibeos/scripts/lane-readiness.py`
- [x] Validate generated lane packets against `plugins/vibeos/reference/lane-packet.schema.json`
- [x] Add synthetic git fixtures for clean ACCEPT, scope-violation DEFER, and rebase-conflict DEFER

### Out of Scope
- Running real parallel VibeOS work lanes
- Changing worktree hook behavior
- Adding Phase 41 agent-team execution

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-114 | Lane return-packet schema | Complete |

## Acceptance Criteria

- [x] AC-1: Clean synthetic lane rebases, runs the gate command, validates packet, and returns `ACCEPT`
- [x] AC-2: Synthetic out-of-scope diff returns `DEFER` with scope defect
- [x] AC-3: Synthetic rebase conflict returns `DEFER`, skips gates, and cleans the scratch worktree
- [x] AC-4: Default gate command integrates `gate-runner.sh wo_exit`
- [x] AC-5: Packet output validates against `lane-packet.schema.json`

## Test Strategy

- **Unit/integration tests:** `python3 -m pytest tests/test_lane_readiness.py`
- **Compile:** `python3 -m py_compile plugins/vibeos/scripts/lane-readiness.py tests/test_lane_readiness.py`
- **Full suite:** `python3 -m pytest tests`
- **Gate proof:** `bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos`

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: Synthetic git fixtures are sufficient for the first deterministic slice; live branch operation stays opt-in via CLI args.
- Test status: Pending at implementation start.

### Pre-Implementation Audit
- Status: `complete`
- Findings: The script must not mutate the primary working tree. All rebase/gate work happens in a scratch worktree that is removed on success or failure.
- Test status: Pending at implementation start.

### Pre-Commit Audit
- Status: `complete`
- Findings: The lane-readiness command mutates only scratch worktrees and writes packet evidence in the project tree. Synthetic fixtures cover the required ACCEPT, scope-violation DEFER, and rebase-conflict DEFER paths.
- Test status: Focused lane-readiness tests passed; full suite passed; `pre_commit` gate passed.

## Evidence

- [x] Implementation complete
- [x] Tests pass
- [x] Gates pass
- [x] Documentation updated

### Proof Commands

```bash
python3 -m py_compile plugins/vibeos/scripts/lane-readiness.py tests/test_lane_readiness.py

python3 -m pytest tests/test_lane_readiness.py
# 4 passed in 1.13s

python3 -m pytest tests
# 162 passed in 38.79s

bash plugins/vibeos/scripts/validate-security-patterns.sh
# PASS: No security anti-patterns detected

bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos
# Total: 10 | Passed: 6 | Failed: 0 | Skipped: 4
# Result: PASS
```
