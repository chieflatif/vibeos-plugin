# WO-098: Runtime Handoff Adapter

## Status

`Complete`

## Phase

Phase 25: Runtime Handoff Adapter

## Objective

Add a dry-run-first Codex/Claude runtime handoff adapter that turns long-run autonomy handoff state into explicit local runtime commands, while launching only when `--execute` is explicitly provided.

## Scope

### In Scope
- [x] Add `autonomy-runtime-adapter.py`
- [x] Generate `.vibeos/autonomy/runtime-adapter-plan.json`
- [x] Read `.vibeos/runtime-capabilities.json`
- [x] Read loop and runner handoff state
- [x] Select Codex or Claude from local capability evidence
- [x] Build stdin prompt handoffs for build or audit roles
- [x] Keep runtime launching behind explicit `--execute`
- [x] Install adapter through bootstrap and upgrade surfaces

### Out of Scope
- Guaranteeing a provider session will run forever
- Bypassing Codex/Claude local permission, auth, or quota behavior
- Cloud queue orchestration or managed worker infrastructure

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-072 | Runtime Capability Matrix | Complete |
| WO-096 | Long-Run Runner Adapter | Complete |
| WO-097 | Long-Run Loop Entrypoint | Complete |

## Findings

1. Local runtime detection shows Codex and Claude can be invoked non-interactively, but the harness must not assume those commands exist on every machine.
2. Handoff state needs a concrete command artifact so external schedulers and future process managers can launch the next model runtime intentionally.
3. Runtime launch must stay dry-run-first because it can spend tokens, edit files, and run tools.

## Acceptance Criteria

- [x] AC-1: Adapter writes `.vibeos/autonomy/runtime-adapter-plan.json`
- [x] AC-2: Adapter selects Codex when capability evidence recommends Codex
- [x] AC-3: Adapter reports `no_handoff` when no loop or runner handoff exists
- [x] AC-4: Adapter keeps launch behind explicit `--execute`
- [x] AC-5: Bootstrap and upgrade paths install the adapter script

## Evidence

- [x] `plugins/vibeos/scripts/autonomy-runtime-adapter.py`
- [x] `tests/test_long_run_autonomy.py`
- [x] `tests/test_codex_bootstrap.py`
- [x] Local runtime help inspected for Codex and Claude non-interactive command support
- [x] Full repository validation run
