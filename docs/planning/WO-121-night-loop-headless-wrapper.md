---
wo: WO-121
title: Night-Loop Headless Wrapper
status: Implemented Locally
phase: 39
phase_name: Loop & Headless Execution
wo_class: harness
write_scope:
  - docs/planning/WO-121-night-loop-headless-wrapper.md
  - docs/planning/WO-INDEX.md
  - docs/evidence/vnext/generated-inventory.json
  - plugins/vibeos/scripts/night-loop.sh
  - tests/test_night_loop.py
no_touch:
  - /Users/latifhorst/latifhorstweb/**
  - /Users/latifhorst/Joan4U/**
required_auditors:
  - correctness-auditor
  - evidence-auditor
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: null
  cost_ceiling_usd: null
---

# WO-121: Night-Loop Headless Wrapper

## Status

`Implemented Locally`

## Phase

Phase 39: Loop & Headless Execution

## Objective

Add a dry-run-first night-loop wrapper for scheduled Claude headless ticks while refusing live execution until Decision D-3 confirms Agent SDK credit availability.

## Source Evidence

- The vNext master plan records D-3 as `OPEN — operator action only`, blocking scheduled live `claude -p` work until Latif confirms the Agent SDK credit.
- Current Claude Code headless docs were checked during Phase 38 work: `claude -p --bare --output-format json` is the planned headless substrate and emits `total_cost_usd`.

## Scope

### In Scope
- [x] Add `plugins/vibeos/scripts/night-loop.sh`
- [x] Make dry-run mode the default
- [x] Run `autonomy-scheduler-guard.py` before planning or executing a night tick
- [x] Refuse live `--execute` when D-3 is not confirmed
- [x] Plan the `claude -p --bare --output-format json` step with allowlisted tools
- [x] Plan the one-tick `autonomy-loop.py` handoff
- [x] Plan full-audit, drift, waiver, and cost-capture steps
- [x] Capture cost into evidence when a headless JSON fixture/path is supplied
- [x] Add deterministic tests for dry-run report, scheduler-guard block, and D-3 live-run refusal

### Out of Scope
- Running a live scheduled headless Claude loop
- Claiming 24-48 hour autonomy proof
- Resolving D-3
- Implementing waiver-expiry scanning before WO-127
- Website changes

## Design Notes

`night-loop.sh` writes `night-loop-report.json` under the evidence directory. In dry-run mode it does not call Claude; it records the planned `claude -p --bare --output-format json` command and planned downstream tick/gate/drift/waiver/cost steps.

Live `--execute` is gated by either:

- `VIBEOS_AGENT_SDK_CREDIT_CONFIRMED=1`
- `.vibeos/config.json` with `decisions.agent_sdk_credit_confirmed: true`

Until then, the script exits 2 with `blocked_agent_sdk_credit_required`. This keeps D-3 truthful.

## Acceptance Criteria

- [x] AC-1: Dry-run mode is default and writes `night-loop-report.json`
- [x] AC-2: Scheduler-guard block exits 2 and records `scheduler_guard_blocked`
- [x] AC-3: Live `--execute` refuses to run while D-3 is open
- [x] AC-4: Cost capture writes `cost-report.json` when headless JSON is supplied
- [x] AC-5: Planned steps include Claude headless, one autonomy loop tick, full audit, drift sweep, waiver check, and cost capture

## Remaining Exit Blocker

- D-3 remains open in the master plan. This WO is intentionally `Implemented Locally`, not `Complete`, until Latif confirms the Agent SDK credit and a live scheduled-run proof can be produced.

## Test Strategy

- **Focused tests:** `python3 -m pytest tests/test_night_loop.py`
- **Full suite:** `python3 -m pytest tests`
- **Gate proof:** `bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos`

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: D-3 is open and operator-owned; implementation must block live scheduled headless runs while still allowing dry-run proof.
- Test status: Pending.

### Pre-Implementation Audit
- Status: `complete`
- Findings: The safe slice is a deterministic wrapper with scheduler-guard proof and cost fixture capture. Live Claude execution remains gated.
- Test status: Pending.

### Pre-Commit Audit
- Status: `complete`
- Findings: The wrapper does not run live Claude in default mode and refuses `--execute` until D-3 is explicitly confirmed. Waiver scan is represented as planned/deferred until WO-127.
- Test status: Focused tests passed; full suite passed; `pre_commit` gate passed.

## Evidence

- [x] Local implementation complete
- [x] Tests pass
- [x] Gates pass
- [x] Documentation updated
- [ ] D-3 live-run prerequisite resolved
- [ ] Live scheduled headless proof produced

### Proof Commands

```bash
python3 -m pytest tests/test_night_loop.py
# 3 passed in 0.33s

python3 plugins/vibeos/scripts/wo-frontmatter-lint.py validate-index --project-dir .
# [wo-frontmatter] PASS: WO-INDEX.md generated block is current

bash plugins/vibeos/scripts/gate-runner.sh wo_entry --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos --wo 121
# Total: 4 | Passed: 2 | Failed: 0 | Skipped: 2
# Result: PASS

python3 -m pytest tests
# 195 passed in 35.22s

bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos
# Total: 10 | Passed: 6 | Failed: 0 | Skipped: 4
# Result: PASS
```
