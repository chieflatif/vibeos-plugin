---
wo: WO-139
title: Session-limit-aware Self-rescheduling
status: Complete
phase: 39
phase_name: Loop & Headless Execution
wo_class: harness
write_scope:
  - docs/planning/WO-139-session-limit-aware-self-rescheduling.md
  - docs/planning/WO-INDEX.md
  - docs/evidence/vnext/generated-inventory.json
  - docs/evidence/vnext/wo-139-limit-aware-scheduler/**
  - plugins/vibeos/scripts/limit-aware-scheduler.py
  - plugins/vibeos/scripts/autonomy-scheduler-profile.py
  - plugins/vibeos/scripts/plugin-upgrade.sh
  - plugins/vibeos/hooks/scripts/limit-warning-capture.sh
  - plugins/vibeos/hooks/hooks.json
  - plugins/vibeos/hook-manifest.json
  - vibeos-init.sh
  - tests/test_long_run_autonomy.py
  - tests/test_hook_lifecycle.py
  - tests/test_status_reconciliation.py
no_touch:
  - /Users/latifhorst/latifhorstweb/**
  - /Users/latifhorst/Joan4U/**
required_auditors:
  - correctness-auditor
  - evidence-auditor
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: 1
  cost_ceiling_usd: 0
loop_goal: provider/session-limit signals write a one-shot non-Claude resume artifact
loop_ceiling_turns: 1
loop_ceiling_cost_usd: 0
---

# WO-139: Session-limit-aware Self-rescheduling

## Status

`Complete`

## Phase

Phase 39: Loop & Headless Execution

## Objective

Add deterministic, no-Claude-dependency session-limit handling that converts Claude Code limit warnings and headless provider-limit failures into reviewed one-shot scheduler artifacts, pauses large dispatches, and marks reactive loops as `PAUSED_FOR_LIMIT` until the reset window.

## Source Evidence

- The vNext master plan requires WO-139 to treat provider/session limits as a pure bash/python/cron control-plane problem: Claude may be the resumed payload, but not the scheduler.
- `autonomy-failure-detector.py` already emits `AUTONOMY-PROVIDER-LIMIT` when runtime output includes rate, quota, session, usage, or 429 limit signals.
- Claude Code hook documentation identifies `Notification` as a standalone hook event whose payload includes `message`, optional `title`, and `notification_type`; Notification hooks are side-effect hooks and cannot block.
- `autonomy-scheduler-profile.py` already creates reviewed scheduler profile files without installing them into the OS or CI provider.

## Scope

### In Scope
- [x] Add `plugins/vibeos/scripts/limit-aware-scheduler.py`
- [x] Add a `Notification` command hook that calls the scheduler only with local payload/state
- [x] Generate one-shot shell, cron, and launchd resume artifacts under `.vibeos/autonomy/limit-aware/`
- [x] Parse reset timestamps from explicit fields, notification text, and retry-after values; use a conservative fallback when absent
- [x] Mark reactive provider-limit failures as `PAUSED_FOR_LIMIT` in `.vibeos/autonomy/loop-state.json`
- [x] Record dispatch policy that blocks new large dispatches after proactive warnings
- [x] Integrate install/upgrade and scheduler-profile surfaces
- [x] Add deterministic tests and evidence fixtures

### Out of Scope
- Installing cron or launchd jobs automatically
- Calling Claude, Codex, or any model from the scheduler itself
- Claiming guaranteed reset accuracy from UI notification text
- Claiming 24-48 hour autonomy proof
- Website changes

## Design Notes

`limit-aware-scheduler.py` consumes one of four local sources:

- `notification`: JSON from Claude Code `Notification` hooks
- `headless-json`: JSON/text emitted by a headless runtime attempt
- `failure-report`: `.vibeos/autonomy/failure-report.json`
- `text`: raw local text

When a limit signal is present, it writes `.vibeos/autonomy/limit-aware/limit-aware-scheduler.json`, appends `limit-events.jsonl`, and generates reviewed one-shot resume artifacts. The generated shell script is guarded by reset time and a one-shot marker before it invokes the existing `night-loop.sh` payload path. The script does not install external schedulers; operators or reviewed automation must install the cron/launchd profile.

The proactive warning path writes a dispatch policy with `large_dispatch_allowed: false` and status `LIMIT_WARNING_SCHEDULED`. The reactive path writes loop-state status `PAUSED_FOR_LIMIT`, preserving recovery-resolution semantics for unrelated recovery actions.

## Acceptance Criteria

- [x] AC-1: Simulated limit notification writes one-shot resume artifacts and a dispatch policy before the hard limit
- [x] AC-2: Simulated headless/provider limit without reset time schedules a conservative fallback and marks loop-state `PAUSED_FOR_LIMIT`
- [x] AC-3: Existing `AUTONOMY-PROVIDER-LIMIT` failure reports are consumed without re-running Claude
- [x] AC-4: Notification hook is registered, documented, non-blocking, and executable in a fixture run
- [x] AC-5: Scheduler-profile output documents the limit-aware one-shot handoff surface
- [x] AC-6: Bootstrap and upgrade surfaces install the new local scheduler and hook script
- [x] AC-7: Generated inventory and WO index reconcile

## Remaining Limitations

- Reset timestamps from human-facing notification text can be approximate or absent; fallback scheduling is deliberately conservative.
- The generated shell/cron/launchd artifacts are reviewed profiles, not automatically installed OS jobs.
- This proves deterministic limit-aware rescheduling artifacts, not continuous 24-48 hour autonomy.

## Test Strategy

- **Focused tests:** `python3 -m pytest tests/test_long_run_autonomy.py tests/test_hook_lifecycle.py tests/test_status_reconciliation.py`
- **Index check:** `python3 plugins/vibeos/scripts/wo-frontmatter-lint.py validate-index --project-dir .`
- **Full suite:** `python3 -m pytest tests`
- **Gate proof:** `bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos`

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: The scheduler must stay pure local control-plane logic; Claude and Codex are only possible resumed payloads through existing reviewed wrappers.
- Test status: Complete.

### Closeout Audit
- Status: `complete`
- Findings: The implementation is deterministic and side-effect bounded. It writes reviewed resume artifacts and local state, but does not install system schedulers or bypass scheduler-guard/recovery-resolution checks.
- Test status: `208 passed`.
