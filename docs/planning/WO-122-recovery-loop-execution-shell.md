---
wo: WO-122
title: Recovery-loop Execution Shell
status: Complete
phase: 39
phase_name: Loop & Headless Execution
wo_class: harness
write_scope:
  - docs/planning/WO-122-recovery-loop-execution-shell.md
  - docs/planning/WO-INDEX.md
  - docs/evidence/vnext/generated-inventory.json
  - docs/evidence/vnext/wo-122-recovery-loop/**
  - plugins/vibeos/scripts/autonomy-recovery-loop.py
  - plugins/vibeos/scripts/autonomy-smoke.py
  - plugins/vibeos/scripts/plugin-upgrade.sh
  - tests/test_long_run_autonomy.py
  - tests/test_codex_bootstrap.py
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
loop_goal: recovery retry is bounded to one attempt per recovery plan generation
loop_ceiling_turns: 1
loop_ceiling_cost_usd: 0
---

# WO-122: Recovery-loop Execution Shell

## Status

`Complete`

## Phase

Phase 39: Loop & Headless Execution

## Objective

Add a deterministic recovery-loop shell that may execute exactly one saved resume-plan retry for a recovery plan, then escalates instead of looping, while leaving recovery-resolution evidence binding unchanged.

## Source Evidence

- The vNext master plan says the recovery loop must wrap the existing autonomy control plane, not rewrite it.
- `autonomy-recovery-planner.py` already creates plan-only recovery actions and must remain plan-only.
- `autonomy-scheduler-guard.py` already blocks unresolved recovery actions.
- `autonomy-recovery-resolution.py` already requires action id, summary, and evidence bound to the current recovery-plan generation before the scheduler guard unblocks.

## Scope

### In Scope
- [x] Add `plugins/vibeos/scripts/autonomy-recovery-loop.py`
- [x] Dry-run by default and write `.vibeos/autonomy/recovery-loop-state.json`
- [x] Execute at most one `autonomy-runner.py --resume-plan ... --execute` retry per `recovery-plan.json` generation
- [x] Append `.vibeos/autonomy/recovery-loop-history.jsonl`
- [x] Escalate without re-running when the same unresolved recovery plan already has a retry attempt
- [x] Preserve scheduler-guard and recovery-resolution semantics
- [x] Add deterministic known-bad fixture coverage
- [x] Add install, upgrade, and smoke coverage

### Out of Scope
- Automatically resolving recovery actions
- Automatically clearing or editing recovery plans
- Launching Claude or Codex directly from the recovery-loop shell
- Bypassing scheduler guard for normal scheduler ticks
- Claiming 24-48 hour autonomy proof
- Website changes

## Design Notes

`autonomy-recovery-loop.py` is a wrapper over the existing local runner. It reads:

- `.vibeos/autonomy/recovery-plan.json`
- `.vibeos/autonomy/recovery-resolution.json`
- `.vibeos/autonomy/resume-plan.json`
- `.vibeos/autonomy/recovery-loop-state.json`

It derives a recovery-plan key from the plan generation timestamp and blocking action ids. Dry-run mode reports the pending retry without consuming the one allowed attempt. Live `--execute` invokes `autonomy-runner.py` against the saved resume plan exactly once for that recovery-plan key.

If the same recovery plan remains unresolved and the wrapper is invoked again, the shell records `escalated_retry_already_attempted` and does not call the runner. It does not write recovery-resolution evidence; operators or higher-level flows must still call `autonomy-recovery-resolution.py` with explicit evidence before scheduler guard unblocks.

## Acceptance Criteria

- [x] AC-1: Dry-run writes recovery-loop state without incrementing attempts
- [x] AC-2: First live retry executes the saved resume plan through `autonomy-runner.py`
- [x] AC-3: Failed first retry is recorded in state/history
- [x] AC-4: Second unresolved invocation escalates and does not execute the runner
- [x] AC-5: Successful retry does not unblock scheduler guard without recovery-resolution evidence
- [x] AC-6: Resolution evidence bound to the recovery-plan generation unblocks scheduler guard
- [x] AC-7: Bootstrap, upgrade, and smoke surfaces include the recovery-loop script
- [x] AC-8: Generated inventory and WO index reconcile

## Remaining Limitations

- The shell executes local allowlisted resume-plan commands only; model/provider resume remains a separate reviewed runtime-adapter concern.
- A successful retry is evidence, not resolution. It still requires `autonomy-recovery-resolution.py`.
- This WO proves bounded recovery retry behavior, not 24-48 hour continuous autonomy.

## Test Strategy

- **Focused tests:** `python3 -m pytest tests/test_long_run_autonomy.py tests/test_codex_bootstrap.py`
- **Index check:** `python3 plugins/vibeos/scripts/wo-frontmatter-lint.py validate-index --project-dir .`
- **Full suite:** `python3 -m pytest tests`
- **Gate proof:** `bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos`

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: The wrapper must not mark recovery actions resolved or bypass scheduler guard; it can only record one bounded retry attempt.
- Test status: Pending.

### Pre-Implementation Audit
- Status: `complete`
- Findings: Reusing `autonomy-runner.py` keeps command allowlisting and resume-plan classification centralized. The retry ledger must key attempts by recovery-plan generation to prevent unbounded repeats.
- Test status: Pending.

### Pre-Commit Audit
- Status: `complete`
- Findings: The wrapper preserves the existing recovery semantics: it does not clear recovery plans, it does not write recovery-resolution evidence, and it does not launch Claude or Codex directly. The retry ledger is keyed by recovery-plan generation and action ids, so a second unresolved invocation escalates without re-executing the runner.
- Test status: Focused tests passed; smoke passed; full suite passed; WO-122 gate passed; `pre_commit` gate passed.

## Evidence

- [x] Implementation complete
- [x] Tests pass
- [x] Gates pass
- [x] Documentation updated
- [x] Known-bad second-attempt escalation trace captured

### Proof Commands

```bash
python3 -m pytest tests/test_long_run_autonomy.py tests/test_codex_bootstrap.py
# 43 passed in 7.09s

python3 plugins/vibeos/scripts/autonomy-smoke.py --runtime-provider none --json
# summary.status: pass
# step_count: 9
# recovery-loop copied and invoked

python3 plugins/vibeos/scripts/autonomy-recovery-loop.py --project-dir "$TMP_ROOT" --execute --json
# known-bad first attempt exit 1
# summary.status: retry_failed

python3 plugins/vibeos/scripts/autonomy-recovery-loop.py --project-dir "$TMP_ROOT" --execute --json
# known-bad second attempt exit 2
# summary.status: escalated_retry_already_attempted
# runner: null

python3 -m pytest tests
# 203 passed in 48.57s

python3 plugins/vibeos/scripts/wo-frontmatter-lint.py validate-index --project-dir .
# [wo-frontmatter] PASS: WO-INDEX.md generated block is current

bash plugins/vibeos/scripts/gate-runner.sh wo_entry --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos --wo 122
# Total: 4 | Passed: 2 | Failed: 0 | Skipped: 2
# Result: PASS

bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos
# Total: 10 | Passed: 6 | Failed: 0 | Skipped: 4
# Result: PASS
```
