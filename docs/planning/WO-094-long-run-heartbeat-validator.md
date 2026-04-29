# WO-094: Long-Run Heartbeat Validator

## Status

`Complete`

## Phase

Phase 21: Long-Run Autonomy

## Objective

Add deterministic scripts that record long-run autonomy heartbeats and validate run cadence, duration, checkpoint, audit, and closeout policy.

## Scope

### In Scope
- [x] Add `autonomy-heartbeat.py`
- [x] Add `validate-long-run-autonomy.py`
- [x] Wire long-run validation into `session_start` and `session_end`
- [x] Add unit coverage for heartbeat creation, stale heartbeat detection, duration policy, and closeout validation
- [x] Ensure bootstraps and plugin upgrade install the new scripts and reference pack

### Out of Scope
- External cron or scheduler integration
- Provider-specific cost-budget APIs
- Cloud deployment automation

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-093 | Long-Run Autonomy Control Plane | Complete |

## Findings

1. A 24-48 hour run without heartbeat artifacts cannot be audited or safely resumed.
2. Long-running autonomous sessions need deterministic stale-run detection rather than relying on narrative status updates.
3. Session closeout should fail if a long-run session is still marked active.

## Acceptance Criteria

- [x] AC-1: Heartbeat script creates `.vibeos/autonomy/heartbeats/*.json`
- [x] AC-2: Heartbeat script updates `.vibeos/config.json`, `.vibeos/session-state.json`, and `.vibeos/build-log.md`
- [x] AC-3: Validator fails stale heartbeat evidence
- [x] AC-4: Validator fails duration above the 48-hour policy cap
- [x] AC-5: Validator passes terminal closeout with `--require-closed`
- [x] AC-6: Gate manifest exposes long-run validation at session start and session end

## Evidence

- [x] `plugins/vibeos/scripts/autonomy-heartbeat.py`
- [x] `plugins/vibeos/scripts/validate-long-run-autonomy.py`
- [x] `tests/test_long_run_autonomy.py`
- [x] `tests/test_gate_runner.py`
- [x] Full repository validation run
