# WO-095: Long-Run Supervisor Resume Plan

## Status

`Complete`

## Phase

Phase 22: Long-Run Supervisor

## Objective

Add a deterministic long-run autonomy supervisor that reads heartbeat/session state, enforces cadence and loop/runtime limits, and writes a resumable command plan for the next loop.

## Scope

### In Scope
- [x] Add `autonomy-supervisor.py`
- [x] Generate `.vibeos/autonomy/resume-plan.json`
- [x] Generate `.vibeos/autonomy/supervisor-state.json`
- [x] Decide between continue, heartbeat, checkpoint, audit, stop, closed, and not-configured states
- [x] Include `next_resume_after` scheduling hints for external schedulers or later sessions
- [x] Add regression coverage for fresh cadence, checkpoint due, audit due, and iteration-limit stop
- [x] Install supervisor through bootstrap and upgrade surfaces

### Out of Scope
- Running as a background daemon
- Launching Claude or Codex processes directly
- External scheduler or cloud automation integration

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-093 | Long-Run Autonomy Control Plane | Complete |
| WO-094 | Long-Run Heartbeat Validator | Complete |

## Findings

1. Heartbeat evidence proves state, but a long-run harness also needs a deterministic decision point between heartbeats.
2. A supervisor should write the next command plan instead of hiding decisions inside model memory.
3. The supervisor must stop on loop/runtime limits and force human/session-audit review rather than silently continuing.

## Acceptance Criteria

- [x] AC-1: Supervisor emits `continue_build` when cadence and failure controls are fresh
- [x] AC-2: Supervisor emits `run_checkpoint` when checkpoint cadence is due
- [x] AC-3: Supervisor emits `run_audit` when audit cadence is due
- [x] AC-4: Supervisor emits `stop` when loop iteration limit is reached
- [x] AC-5: Supervisor writes `resume-plan.json` and `supervisor-state.json`
- [x] AC-6: Supervisor writes `next_resume_after` for scheduled resume attempts
- [x] AC-7: Bootstrap and upgrade paths install the supervisor script

## Evidence

- [x] `plugins/vibeos/scripts/autonomy-supervisor.py`
- [x] `tests/test_long_run_autonomy.py`
- [x] Full repository validation run
