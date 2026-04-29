# WO-096: Long-Run Runner Adapter

## Status

`Complete`

## Phase

Phase 23: Long-Run Runner Adapter

## Objective

Add a safe runner adapter that reads `.vibeos/autonomy/resume-plan.json`, classifies each command, executes only allowlisted local VibeOS script commands, and records a durable runner report for blocked commands and Codex/Claude handoff work.

## Scope

### In Scope
- [x] Add `autonomy-runner.py`
- [x] Generate `.vibeos/autonomy/runner-report.json`
- [x] Dry-run classify resume plans by default
- [x] Execute allowlisted local VibeOS commands only when `--execute` is passed
- [x] Block untrusted shell commands and shell control tokens
- [x] Mark natural-language Codex/Claude continuation steps as handoff-required work
- [x] Install runner through bootstrap and upgrade surfaces

### Out of Scope
- Launching Claude or Codex processes directly
- Running arbitrary shell commands from resume plans
- External cron, daemon, or cloud scheduler integration

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-093 | Long-Run Autonomy Control Plane | Complete |
| WO-094 | Long-Run Heartbeat Validator | Complete |
| WO-095 | Long-Run Supervisor Resume Plan | Complete |

## Findings

1. The supervisor can write a deterministic resume plan, but without a runner adapter that plan still depends on model memory or manual interpretation.
2. A resume runner must not become an arbitrary shell execution surface, especially in a harness intended to survive adversarial review.
3. Codex/Claude continuation instructions are runtime handoffs, not shell commands; the harness should report them truthfully.

## Acceptance Criteria

- [x] AC-1: Runner reads `.vibeos/autonomy/resume-plan.json`
- [x] AC-2: Runner writes `.vibeos/autonomy/runner-report.json`
- [x] AC-3: Runner dry-run classifies executable, blocked, and handoff-required commands
- [x] AC-4: Runner executes allowlisted heartbeat commands with `--execute`
- [x] AC-5: Runner blocks untrusted commands such as `rm -rf .`
- [x] AC-6: Bootstrap and upgrade paths install the runner script

## Evidence

- [x] `plugins/vibeos/scripts/autonomy-runner.py`
- [x] `tests/test_long_run_autonomy.py`
- [x] `tests/test_codex_bootstrap.py`
- [x] Full repository validation run
