---
wo: WO-121
title: Night-Loop Headless Wrapper
status: Complete
phase: 39
phase_name: Loop & Headless Execution
wo_class: harness
write_scope:
  - docs/planning/WO-121-night-loop-headless-wrapper.md
  - docs/planning/WO-INDEX.md
  - docs/evidence/vnext/generated-inventory.json
  - docs/evidence/vnext/wo-121-night-loop-live/**
  - plugins/vibeos/scripts/autonomy-loop.py
  - plugins/vibeos/scripts/night-loop.sh
  - tests/test_long_run_autonomy.py
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

`Complete`

## Phase

Phase 39: Loop & Headless Execution

## Objective

Add a dry-run-first night-loop wrapper for scheduled Claude headless ticks while refusing live execution until Decision D-3 confirms Agent SDK credit availability, then prove the logged-in Claude subscription path with cost-captured evidence.

## Source Evidence

- The vNext master plan records D-3 as `OPEN — operator action only`, blocking scheduled live `claude -p` work until Latif confirms the Agent SDK credit.
- Current Claude Code headless docs were checked during Phase 38 work: `claude -p --bare --output-format json` is the planned headless substrate and emits `total_cost_usd`.
- Local Claude Code 2.1.177 help now states `--bare` does not read OAuth/keychain auth and requires `ANTHROPIC_API_KEY` or `apiKeyHelper` via `--settings`; logged-in Claude plan credit therefore needs the subscription-auth headless path instead of forced `--bare`.
- `claude auth status` confirms local subscription auth is available with `authMethod: claude.ai` and `subscriptionType: max`.

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
- [x] Preserve failed live headless JSON, stderr, and cost evidence when Claude exits nonzero
- [x] Default live headless execution to subscription auth, `sonnet`, `--safe-mode`, and a `$1.00` max budget ceiling
- [x] Keep `api-key-bare` mode guarded for API-key or `apiKeyHelper` use only
- [x] Let framework-repo autonomy loops fall back to sibling `plugins/vibeos/scripts` when `.vibeos/scripts` is not installed
- [x] Add deterministic tests for dry-run report, scheduler-guard block, and D-3 live-run refusal
- [x] Produce a live subscription-auth headless run with cost capture and a one-tick autonomy loop

### Out of Scope
- Claiming 24-48 hour autonomy proof
- Marking D-3 durably resolved in repo config or the master plan
- Implementing waiver-expiry scanning before WO-127
- Website changes

## Design Notes

`night-loop.sh` writes `night-loop-report.json` under the evidence directory. In dry-run mode it does not call Claude; it records the planned `claude -p --output-format json` command and planned downstream tick/gate/drift/waiver/cost steps.

The default live command uses subscription-authenticated Claude Code with:

- `--model sonnet`
- `--safe-mode`
- `--max-budget-usd 1.00`
- `--no-session-persistence`

The previous forced `--bare` command is retained only behind `--headless-auth-mode api-key-bare`, and that mode refuses to execute unless `ANTHROPIC_API_KEY` or `--claude-settings` is present. This is intentional: local Claude Code help states that `--bare` skips OAuth/keychain auth.

Live `--execute` is gated by either:

- `VIBEOS_AGENT_SDK_CREDIT_CONFIRMED=1`
- `.vibeos/config.json` with `decisions.agent_sdk_credit_confirmed: true`

Until then, the script exits 2 with `blocked_agent_sdk_credit_required`. This keeps D-3 truthful.

## Acceptance Criteria

- [x] AC-1: Dry-run mode is default and writes `night-loop-report.json`
- [x] AC-2: Scheduler-guard block exits 2 and records `scheduler_guard_blocked`
- [x] AC-3: Live `--execute` refuses to run while D-3 is open
- [x] AC-4: Cost capture writes `cost-report.json` when headless JSON is supplied or failed live headless output still includes `total_cost_usd`
- [x] AC-5: Planned steps include Claude headless, one autonomy loop tick, full audit, drift sweep, waiver check, and cost capture
- [x] AC-6: Subscription-auth mode checks `claude auth status` and records auth method/provider/subscription type without secrets
- [x] AC-7: API-key bare mode refuses live execution without an API key or `apiKeyHelper` settings
- [x] AC-8: Framework-repo autonomy loop can resolve supervisor/runner scripts without a local `.vibeos/scripts` install
- [x] AC-9: Live scheduled headless proof passes with cost capture and one autonomy-loop tick

## Remaining Limitations

- Latif authorized a live attempt on 2026-06-14 by saying `ok go`, and the wrapper ran with `VIBEOS_AGENT_SDK_CREDIT_CONFIRMED=1`.
- The live proof passed with local Claude subscription auth after replacing forced `--bare` with subscription mode.
- The one-tick autonomy loop returned `not_configured` because this plugin repo does not currently have long-run autonomy enabled. That proves the runner path works; it does not prove 24-48 hour autonomy.
- D-3 is operator-confirmed for this live attempt, but this WO does not durably rewrite `.vibeos/config.json` or the master plan decision record.
- Cost values remain estimate-only and must be reconciled against provider billing before public cost claims.

## Test Strategy

- **Focused tests:** `python3 -m pytest tests/test_night_loop.py`
- **Full suite:** `python3 -m pytest tests`
- **Gate proof:** `bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos`

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: D-3 was open and operator-owned at planning time; implementation must block live scheduled headless runs while still allowing dry-run proof.
- Test status: Pending.

### Pre-Implementation Audit
- Status: `complete`
- Findings: The safe slice is a deterministic wrapper with scheduler-guard proof and cost fixture capture. Live Claude execution remains gated.
- Test status: Pending.

### Pre-Commit Audit
- Status: `complete`
- Findings: The wrapper does not run live Claude in default mode and refuses `--execute` until D-3 is explicitly confirmed. Forced `--bare` was corrected because Claude Code 2.1.177 states bare mode cannot use OAuth/keychain login. The live proof now uses subscription auth, `sonnet`, safe mode, and a budget ceiling; cost evidence was captured. Waiver scan is represented as planned/deferred until WO-127.
- Test status: Focused auth/night-loop/autonomy tests passed; full suite passed; WO-121 gate passed; `pre_commit` gate passed.

## Evidence

- [x] Local implementation complete
- [x] Tests pass
- [x] Gates pass
- [x] Documentation updated
- [x] D-3 operator live-attempt authorization received
- [x] Failed live-attempt evidence captured with zero reported cost
- [x] Claude Code subscription-auth headless path available
- [x] Live scheduled headless proof produced
- [x] Live cost evidence captured
- [x] One-tick autonomy loop executed

### Proof Commands

```bash
claude auth status
# loggedIn: true
# authMethod: claude.ai
# subscriptionType: max

python3 -m pytest tests/test_night_loop.py tests/test_long_run_autonomy.py
# 42 passed in 5.25s

VIBEOS_AGENT_SDK_CREDIT_CONFIRMED=1 bash plugins/vibeos/scripts/night-loop.sh --project-dir . --framework-dir plugins/vibeos --evidence-dir docs/evidence/vnext/wo-121-night-loop-live --execute --json
# exit 0
# summary.status: pass
# claude_headless: pass
# live_cost_capture: pass
# live_autonomy_loop: pass
# cost-report.json total_cost_usd: 0.1737791

python3 plugins/vibeos/scripts/wo-frontmatter-lint.py validate-index --project-dir .
# [wo-frontmatter] PASS: WO-INDEX.md generated block is current

bash plugins/vibeos/scripts/gate-runner.sh wo_entry --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos --wo 121
# Total: 4 | Passed: 2 | Failed: 0 | Skipped: 2
# Result: PASS

python3 -m pytest tests
# 200 passed in 47.53s

bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos
# Total: 10 | Passed: 6 | Failed: 0 | Skipped: 4
# Result: PASS
```
