---
wo: WO-120
title: Lane-Loop Ceilings + Goal-Verified Stop
status: Complete
phase: 39
phase_name: Loop & Headless Execution
wo_class: harness
write_scope:
  - docs/planning/WO-120-lane-loop-ceilings-goal-verified-stop.md
  - docs/planning/WO-INDEX.md
  - docs/evidence/vnext/generated-inventory.json
  - plugins/vibeos/hooks/hooks.json
  - plugins/vibeos/hook-manifest.json
  - plugins/vibeos/hooks/scripts/lane-loop-stop.sh
  - plugins/vibeos/skills/build/SKILL.md
  - plugins/vibeos/reference/session-state-schema.md
  - tests/test_lane_loop_stop.py
  - tests/test_status_reconciliation.py
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
loop_goal: pre_commit gate passed
loop_ceiling_turns: 2
---

# WO-120: Lane-Loop Ceilings + Goal-Verified Stop

## Status

`Complete`

## Phase

Phase 39: Loop & Headless Execution

## Objective

Add bounded in-session lane-loop Stop behavior so loop continuation is capped by WO frontmatter and terminal success requires captured gate/test evidence rather than assistant text.

## Scope

### In Scope
- [x] Register `plugins/vibeos/hooks/scripts/lane-loop-stop.sh` as a `Stop` command hook
- [x] Read `loop_goal` and `loop_ceiling_turns` from active WO frontmatter
- [x] Verify loop goals from `.vibeos/hook-events/gate-results.jsonl`
- [x] Ignore assistant completion claims when matching gate/test evidence is missing
- [x] Record `STALLED_AT_CEILING` in `.vibeos/session-state.json`
- [x] Update `plugins/vibeos/skills/build/SKILL.md` with lane-loop status handling
- [x] Update `plugins/vibeos/reference/session-state-schema.md` with `lane_loop` state
- [x] Add fixture tests for block-before-ceiling, stop-at-ceiling, and verified-goal allow

### Out of Scope
- Night-loop headless execution (`WO-121`)
- Recovery-loop resume shell (`WO-122`)
- Cost ceilings and headless cost accumulation
- Running live Claude loops
- Codex hook parity
- Website changes

## Design Notes

`lane-loop-stop.sh` runs after Stop events and is inert unless the active WO frontmatter contains both `loop_goal` and `loop_ceiling_turns`. It increments `.vibeos/session-state.json` `lane_loop.turn_count`, checks captured gate/test evidence, and returns:

- `block` before the ceiling when the goal lacks evidence
- `allow` with `GOAL_VERIFIED` when matching gate/test evidence exists
- `allow` with `STALLED_AT_CEILING` when the ceiling is reached without evidence

The hook intentionally does not parse or trust assistant response text. The fixture includes an assistant-style completion claim in the WO body, and the hook still blocks until evidence exists or the ceiling is reached.

## Acceptance Criteria

- [x] AC-1: `hooks.json` registers `lane-loop-stop.sh` under `Stop`
- [x] AC-2: Hook manifest documents the configured command hook
- [x] AC-3: Fixture WO with `loop_ceiling_turns: 2` blocks on turn 1 without gate evidence
- [x] AC-4: Same fixture records `STALLED_AT_CEILING` and allows stop on turn 2
- [x] AC-5: Matching passing gate evidence records `GOAL_VERIFIED` and allows stop
- [x] AC-6: Build skill and session-state schema document the new status surface
- [x] AC-7: Generated inventory and WO index reconcile

## Test Strategy

- **Focused tests:** `python3 -m pytest tests/test_lane_loop_stop.py tests/test_status_reconciliation.py`
- **Index check:** `python3 plugins/vibeos/scripts/wo-frontmatter-lint.py validate-index --project-dir .`
- **Full suite:** `python3 -m pytest tests`
- **Gate proof:** `bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos`

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: The Stop hook must not trust assistant text. The deterministic evidence source available after WO-116 is `.vibeos/hook-events/gate-results.jsonl`.
- Test status: Pending.

### Pre-Implementation Audit
- Status: `complete`
- Findings: A sibling Stop hook is safer than expanding the code-quality hook. The hook should allow stop at the ceiling rather than block forever.
- Test status: Pending.

### Pre-Commit Audit
- Status: `complete`
- Findings: Loop state is session-state only; WO files are not mutated by the hook. `STALLED_AT_CEILING` is recorded as runtime state and remains distinct from `Complete`.
- Test status: Focused tests passed; full suite passed; `pre_commit` gate passed.

## Evidence

- [x] Implementation complete
- [x] Tests pass
- [x] Gates pass
- [x] Documentation updated

### Proof Commands

```bash
python3 -m pytest tests/test_lane_loop_stop.py tests/test_status_reconciliation.py
# 9 passed in 0.39s

python3 plugins/vibeos/scripts/wo-frontmatter-lint.py validate-index --project-dir .
# [wo-frontmatter] PASS: WO-INDEX.md generated block is current

bash plugins/vibeos/scripts/gate-runner.sh wo_entry --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos --wo 120
# Total: 4 | Passed: 2 | Failed: 0 | Skipped: 2
# Result: PASS

python3 -m pytest tests
# 192 passed in 34.63s

bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos
# Total: 10 | Passed: 6 | Failed: 0 | Skipped: 4
# Result: PASS
```
