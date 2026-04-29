# WO-103: Autonomy Recovery Planner

## Status

`Complete`

## Phase

Phase 30: Autonomy Recovery Planner

## Objective

Convert autonomy failure detector findings into safe, auditable recovery actions before another scheduler tick repeats the same broken path.

## Scope

### In Scope
- [x] Add `autonomy-recovery-planner.py`
- [x] Write `.vibeos/autonomy/recovery-plan.json`
- [x] Map repeated handoff findings to runtime handoff planning
- [x] Map repeated no-progress decisions to supervisor/runner inspection
- [x] Map consecutive failures to scheduler pause and session audit
- [x] Map lease conflicts to lease-owner review without automatic deletion
- [x] Map blocked runner reports to resume-plan repair
- [x] Map runtime failures to capability refresh and adapter replanning
- [x] Map provider/session limits to blocked heartbeat and fresh-session resume
- [x] Include recovery planner in disposable smoke targets
- [x] Provide recovery-plan evidence that the scheduler guard can block on

### Out of Scope
- Automatically clearing active leases
- Automatically installing or disabling external schedulers
- Automatically launching Codex or Claude providers
- Retrying provider/session limit failures in a tight loop

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-098 | Runtime Handoff Adapter | Complete |
| WO-100 | Disposable Autonomy Smoke | Complete |
| WO-101 | Autonomy Run Lease Guard | Complete |
| WO-102 | Autonomy Failure Loop Detector | Complete |

## Findings

1. Failure detection is not enough for 24-48 hour autonomy; the harness needs a deterministic next response.
2. Recovery must preserve autonomy while avoiding unsafe automatic actions such as clearing leases or launching providers without review.
3. Provider/session limits should result in preserved state and fresh-session resume planning rather than cost or time budget accounting.

## Acceptance Criteria

- [x] AC-1: Planner passes clean failure reports
- [x] AC-2: Planner maps repeated handoff to runtime handoff planning
- [x] AC-3: Planner maps provider/session limits to scheduler pause and blocked heartbeat command
- [x] AC-4: Planner writes `.vibeos/autonomy/recovery-plan.json`
- [x] AC-5: Smoke chain runs the planner after the detector
- [x] AC-6: Bootstrap and upgrade paths install the planner
- [x] AC-7: Recovery plan exposes blocking action counts for scheduler guard enforcement

## Evidence

- [x] `plugins/vibeos/scripts/autonomy-recovery-planner.py`
- [x] `plugins/vibeos/scripts/autonomy-smoke.py`
- [x] `tests/test_long_run_autonomy.py`
- [x] `tests/test_codex_bootstrap.py`
- [x] Focused autonomy/bootstrap validation run
