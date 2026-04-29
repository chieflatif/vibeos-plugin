# WO-101: Autonomy Run Lease Guard

## Status

`Complete`

## Phase

Phase 28: Autonomy Run Lease Guard

## Objective

Prevent concurrent schedulers or runtime adapters from driving the same long-run autonomy session at the same time.

## Scope

### In Scope
- [x] Add shared `autonomy_lease.py`
- [x] Write `.vibeos/autonomy/run-lease.json` while an autonomy driver is active
- [x] Write `.vibeos/autonomy/last-lease.json` when a driver releases the lease
- [x] Write `.vibeos/autonomy/lease-conflict.json` when a second live driver is blocked
- [x] Recover expired leases deterministically
- [x] Guard `autonomy-loop.py`
- [x] Guard `autonomy-runtime-adapter.py`
- [x] Include lease module in disposable smoke targets

### Out of Scope
- Distributed locking across multiple machines without shared filesystem semantics
- Killing processes that own stale leases
- Provider-level cancellation of Codex or Claude sessions

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-097 | Long-Run Loop Entrypoint | Complete |
| WO-098 | Runtime Handoff Adapter | Complete |
| WO-100 | Disposable Autonomy Smoke | Complete |

## Findings

1. Scheduler profiles and runtime adapters can be invoked by more than one process.
2. Without a lease, two schedulers can both read the same heartbeat state, both choose the same next action, and both mutate the same autonomy artifacts.
3. The guard must recover stale leases so a crashed process does not permanently block the run.

## Acceptance Criteria

- [x] AC-1: Loop driver exits with `lease_conflict` when another live lease exists
- [x] AC-2: Runtime adapter exits with `lease_conflict` when another live lease exists
- [x] AC-3: Expired leases are recovered and recorded in `last-lease.json`
- [x] AC-4: Released leases remove `run-lease.json`
- [x] AC-5: Smoke targets include the shared lease module
- [x] AC-6: Bootstrap and upgrade paths install the lease module

## Evidence

- [x] `plugins/vibeos/scripts/autonomy_lease.py`
- [x] `plugins/vibeos/scripts/autonomy-loop.py`
- [x] `plugins/vibeos/scripts/autonomy-runtime-adapter.py`
- [x] `plugins/vibeos/scripts/autonomy-smoke.py`
- [x] `tests/test_long_run_autonomy.py`
- [x] Full repository validation run
