# WO-102: Autonomy Failure Loop Detector

## Status

`Complete`

## Phase

Phase 29: Autonomy Failure Loop Detector

## Objective

Detect repeated no-progress autonomy loops and operational failures before a scheduler keeps running the same broken path.

## Scope

### In Scope
- [x] Add `autonomy-failure-detector.py`
- [x] Write `.vibeos/autonomy/failure-report.json`
- [x] Read loop and runtime adapter history
- [x] Flag repeated handoff loops
- [x] Flag repeated no-progress decisions
- [x] Flag consecutive blocked or failed control-plane attempts
- [x] Flag active/repeated lease conflicts
- [x] Flag blocked or failed runner reports
- [x] Flag failed runtime adapter reports
- [x] Flag provider/session limit text in runtime output
- [x] Include detector in disposable smoke targets

### Out of Scope
- Token, cost, or elapsed-time budget accounting
- Automatic lease deletion while a live owner exists
- Automatic provider/session switching without reviewed runtime capability evidence

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-097 | Long-Run Loop Entrypoint | Complete |
| WO-098 | Runtime Handoff Adapter | Complete |
| WO-100 | Disposable Autonomy Smoke | Complete |
| WO-101 | Autonomy Run Lease Guard | Complete |

## Findings

1. A scheduler can repeatedly stop at `handoff_required` without actually resuming a model runtime.
2. Runner, runtime, and lease failures can repeat across ticks unless their history is preserved and inspected.
3. Provider/session limit messages are operational blockers, but they should be tracked as failures rather than as general token, cost, or time budgets.

## Acceptance Criteria

- [x] AC-1: Detector passes clean scheduled history
- [x] AC-2: Detector fails repeated handoff loops
- [x] AC-3: Detector fails provider/session limit output
- [x] AC-4: Detector reports latest blocked runner and failed runtime state
- [x] AC-5: Smoke chain runs the detector after validator
- [x] AC-6: Bootstrap and upgrade paths install the detector

## Evidence

- [x] `plugins/vibeos/scripts/autonomy-failure-detector.py`
- [x] `plugins/vibeos/scripts/autonomy-loop.py`
- [x] `plugins/vibeos/scripts/autonomy-runtime-adapter.py`
- [x] `plugins/vibeos/scripts/autonomy-smoke.py`
- [x] `tests/test_long_run_autonomy.py`
- [x] `tests/test_codex_bootstrap.py`
- [x] Focused autonomy/bootstrap validation run
