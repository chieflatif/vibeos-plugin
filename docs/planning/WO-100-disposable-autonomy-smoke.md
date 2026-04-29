# WO-100: Disposable Autonomy Smoke

## Status

`Complete`

## Phase

Phase 27: Disposable Autonomy Smoke

## Objective

Add a disposable autonomy smoke command that proves the heartbeat, loop, runtime-adapter planning, validator, failure-detector, recovery-planner, and scheduler-guard chain works in a fresh target before a scheduler profile is trusted.

## Scope

### In Scope
- [x] Add `autonomy-smoke.py`
- [x] Copy the required autonomy scripts into a disposable or specified target
- [x] Run heartbeat evidence creation
- [x] Run a scheduler-safe loop tick
- [x] Run runtime-adapter planning without launching a model by default
- [x] Run long-run autonomy validation
- [x] Run autonomy failure detection
- [x] Run autonomy recovery planning
- [x] Run autonomy scheduler guarding
- [x] Write `.vibeos/autonomy/smoke-report.json`
- [x] Install smoke command through bootstrap and upgrade surfaces

### Out of Scope
- Launching Codex or Claude by default
- Proving provider auth, provider/session capacity, or model quality
- Installing scheduler jobs

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-094 | Long-Run Heartbeat Validator | Complete |
| WO-097 | Long-Run Loop Entrypoint | Complete |
| WO-098 | Runtime Handoff Adapter | Complete |
| WO-099 | Autonomy Scheduler Profiles | Complete |

## Findings

1. Scheduler profiles should not be trusted until the target can prove the VibeOS autonomy chain runs end to end.
2. A smoke test must use a disposable target by default so validation does not mutate the active project unexpectedly.
3. Model launch must stay opt-in because it can use provider/session capacity and modify files.

## Acceptance Criteria

- [x] AC-1: Smoke command creates or uses a target project directory
- [x] AC-2: Smoke command writes `.vibeos/autonomy/smoke-report.json`
- [x] AC-3: Smoke command runs heartbeat, loop, adapter, validator, failure-detector, recovery-planner, and scheduler-guard steps
- [x] AC-4: Smoke command succeeds without launching Codex or Claude
- [x] AC-5: Bootstrap and upgrade paths install the smoke command

## Evidence

- [x] `plugins/vibeos/scripts/autonomy-smoke.py`
- [x] `tests/test_long_run_autonomy.py`
- [x] `tests/test_codex_bootstrap.py`
- [x] Full repository validation run
