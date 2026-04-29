# WO-105: Autonomy Recovery Resolution Protocol

## Status

`Complete`

## Phase

Phase 32: Autonomy Recovery Resolution Protocol

## Objective

Record evidence-backed resolution for recovery-plan actions before scheduler ticks resume.

## Scope

### In Scope
- [x] Add `autonomy-recovery-resolution.py`
- [x] Write `.vibeos/autonomy/recovery-resolution.json`
- [x] Append `.vibeos/autonomy/recovery-resolution-history.jsonl`
- [x] Require action id, summary, and evidence when recording a resolution
- [x] Bind resolutions to the current recovery plan `generated_at`
- [x] Make `autonomy-scheduler-guard.py` pass resolved recovery plans and block unresolved actions
- [x] Make `autonomy-loop.py` honor resolution evidence before scheduler-safe ticks
- [x] Include recovery resolution in disposable smoke, bootstrap, upgrade, reference, and skill surfaces

### Out of Scope
- Automatically editing or clearing `.vibeos/autonomy/recovery-plan.json`
- Automatically deciding that a recovery action is resolved without explicit evidence
- Automatically launching providers, clearing leases, or disabling external schedulers

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-100 | Disposable Autonomy Smoke | Complete |
| WO-103 | Autonomy Recovery Planner | Complete |
| WO-104 | Autonomy Scheduler Guard | Complete |

## Findings

1. A guard can block a scheduler tick, but it also needs deterministic evidence to know when the same recovery plan is safe to resume.
2. Stale resolution evidence must not unblock a newly generated recovery plan with the same action id.
3. The recovery plan should remain immutable recovery intent; resolution evidence belongs in a separate artifact.

## Acceptance Criteria

- [x] AC-1: Resolution status passes when no recovery actions exist
- [x] AC-2: Recording a resolution requires a known action id, summary, and evidence
- [x] AC-3: Resolution evidence is bound to the current recovery plan generation
- [x] AC-4: Scheduler guard passes a resolved recovery plan and blocks unresolved actions
- [x] AC-5: Loop guard passes resolved recovery actions by default
- [x] AC-6: Smoke, bootstrap, upgrade, docs, and skills include the resolution protocol

## Evidence

- [x] `plugins/vibeos/scripts/autonomy-recovery-resolution.py`
- [x] `plugins/vibeos/scripts/autonomy-scheduler-guard.py`
- [x] `plugins/vibeos/scripts/autonomy-loop.py`
- [x] `plugins/vibeos/scripts/autonomy-smoke.py`
- [x] `tests/test_long_run_autonomy.py`
- [x] `tests/test_codex_bootstrap.py`
- [x] Focused autonomy/bootstrap validation run
