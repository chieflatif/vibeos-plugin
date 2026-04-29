# WO-097: Long-Run Loop Entrypoint

## Status

`Complete`

## Phase

Phase 24: Long-Run Loop Entrypoint

## Objective

Add a scheduler-safe long-run loop entrypoint that runs supervisor plus runner ticks, writes durable loop state, and stops truthfully at blocked, failed, scheduled, terminal, or model-handoff boundaries.

## Scope

### In Scope
- [x] Add `autonomy-loop.py`
- [x] Generate `.vibeos/autonomy/loop-state.json`
- [x] Run supervisor and runner as subprocesses with JSON reports
- [x] Support dry-run classification by default
- [x] Support `--execute` for allowlisted local VibeOS script commands through `autonomy-runner.py`
- [x] Stop at model-handoff boundaries instead of pretending shell automation can do model reasoning
- [x] Install loop entrypoint through bootstrap and upgrade surfaces

### Out of Scope
- Installing cron, launchd, GitHub Actions, or cloud scheduler jobs
- Launching Claude or Codex directly
- Running arbitrary shell commands from resume plans

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-093 | Long-Run Autonomy Control Plane | Complete |
| WO-095 | Long-Run Supervisor Resume Plan | Complete |
| WO-096 | Long-Run Runner Adapter | Complete |

## Findings

1. Supervisor and runner artifacts are enough for deterministic decisions, but a 24-48 hour harness also needs a stable process entrypoint for external schedulers or future runtime adapters.
2. The loop entrypoint must default to one tick so it can be safely invoked repeatedly without hiding infinite execution in a shell process.
3. Model continuation must remain a first-class handoff state, not a fabricated local command.

## Acceptance Criteria

- [x] AC-1: Loop script writes `.vibeos/autonomy/loop-state.json`
- [x] AC-2: Loop script records supervisor and runner JSON output per tick
- [x] AC-3: Loop script stops at `handoff_required`
- [x] AC-4: Loop script can execute a due heartbeat tick through the safe runner
- [x] AC-5: Bootstrap and upgrade paths install the loop script

## Evidence

- [x] `plugins/vibeos/scripts/autonomy-loop.py`
- [x] `tests/test_long_run_autonomy.py`
- [x] `tests/test_codex_bootstrap.py`
- [x] Full repository validation run
