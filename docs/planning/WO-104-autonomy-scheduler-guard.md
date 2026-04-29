# WO-104: Autonomy Scheduler Guard

## Status

`Complete`

## Phase

Phase 31: Autonomy Scheduler Guard

## Objective

Block scheduler-driven autonomy ticks while unresolved recovery actions remain.

## Scope

### In Scope
- [x] Add `autonomy-scheduler-guard.py`
- [x] Write `.vibeos/autonomy/scheduler-guard-report.json`
- [x] Block when `.vibeos/autonomy/recovery-plan.json` has unresolved blocking actions
- [x] Block when `.vibeos/autonomy/failure-report.json` has blocking findings but no recovery plan exists
- [x] Make generated shell, cron, launchd, and GitHub Actions profiles call the guard before loop ticks
- [x] Make `autonomy-loop.py` honor unresolved recovery state directly
- [x] Include guard in disposable smoke targets

### Out of Scope
- Automatically resolving recovery actions
- Automatically clearing or editing recovery plans
- Installing, disabling, or deleting external scheduler jobs
- Bypassing recovery state except through explicit reviewed loop invocation

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-099 | Autonomy Scheduler Profiles | Complete |
| WO-100 | Disposable Autonomy Smoke | Complete |
| WO-102 | Autonomy Failure Loop Detector | Complete |
| WO-103 | Autonomy Recovery Planner | Complete |

## Findings

1. A recovery plan can say the scheduler must pause, but external schedulers need an explicit pre-tick guard to enforce that state.
2. `autonomy-loop.py` also needs direct recovery-state awareness so hand-written invocations do not bypass generated profile safety.
3. Blocking failure reports without recovery plans should stop ticks and force recovery planning before further autonomous execution.

## Acceptance Criteria

- [x] AC-1: Guard passes when no blocking recovery state exists
- [x] AC-2: Guard blocks unresolved recovery plans
- [x] AC-3: Loop blocks unresolved recovery plans by default
- [x] AC-4: Generated scheduler profiles invoke the guard before loop ticks
- [x] AC-5: Smoke chain runs the guard after recovery planning
- [x] AC-6: Bootstrap and upgrade paths install the guard

## Evidence

- [x] `plugins/vibeos/scripts/autonomy-scheduler-guard.py`
- [x] `plugins/vibeos/scripts/autonomy-loop.py`
- [x] `plugins/vibeos/scripts/autonomy-scheduler-profile.py`
- [x] `plugins/vibeos/scripts/autonomy-smoke.py`
- [x] `tests/test_long_run_autonomy.py`
- [x] `tests/test_codex_bootstrap.py`
- [x] Focused autonomy/bootstrap validation run
