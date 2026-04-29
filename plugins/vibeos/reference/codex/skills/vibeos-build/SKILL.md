---
name: vibeos-build
description: Autonomous VibeOS work-order execution for Codex. Use when the user says continue, resume, keep going, build the next thing, start implementing, or wants progress against the current VibeOS plan.
---

# VibeOS Build

Use this skill to execute the next eligible Work Order, or a named WO, end to end.

## Workflow

1. Read:
   - `docs/USER-COMMUNICATION-CONTRACT.md`
   - `docs/planning/DEVELOPMENT-PLAN.md`
   - `docs/planning/WO-INDEX.md`
   - target WO file
   - `.vibeos/config.json`
   - `.vibeos/session-state.json`
   - `.vibeos/checkpoints/*.json`
   - `.vibeos/autonomy/heartbeats/*.json` when long-run autonomy is active
   - `.vibeos/runtime-capabilities.json` when present
2. Determine the active WO and whether a checkpoint already exists.
3. Refresh runtime capabilities before choosing orchestration:

```bash
bash ".vibeos/scripts/detect-runtime-capabilities.sh" --project-dir "."
```

4. Run the build phases yourself, using the current Codex surface available in this project:
   - `investigator.md`
   - `tester.md`
   - `prompt-engineer.md` when prompts or instruction assets change
   - `backend.md` and/or `frontend.md`
   - `doc-writer.md`
   - focused auditors when a WO needs extra scrutiny
   - flow auditor/contract when user journeys, frontend/backend handoffs, auth/session continuity, data side effects, or objective fidelity are affected
   - system invariant auditor/contract when state transitions, ownership, idempotency, recovery, jobs, webhooks, or external side effects are affected
   - dependency intelligence auditor/contract when dependency manifests, lockfiles, package managers, runtimes, SDKs, frameworks, or high-impact packages are affected
   - delivery infrastructure auditor/contract when CI/CD, deployment, environment/secrets, observability, smoke/health checks, rollback, runbooks, or operational scripts are affected
5. Maintain truthful state in:
   - `.vibeos/build-log.md`
   - `.vibeos/checkpoints/WO-*.json`
   - `.vibeos/session-state.json`
   - `.vibeos/autonomy/heartbeats/*.json` for 24-48 hour autonomous runs
6. Run shared gates:
   - `bash ".vibeos/scripts/gate-runner.sh" pre_commit --continue-on-failure`
   - `bash ".vibeos/scripts/gate-runner.sh" wo_exit --continue-on-failure` before true WO closeout
7. Only mark a WO `Complete` when behavior, real-path verification, primary user-flow impact where relevant, objective fidelity where relevant, affected system invariants where relevant, dependency intelligence where relevant, delivery infrastructure where relevant, tests, and blocking gates are all evidenced.
8. If the user wants no routine check-ins, use `vibeos-autonomous`.

## Long-Run Autonomy Rules

When `.vibeos/config.json` has `autonomy.long_run.active = true`:
- Record a heartbeat with `.vibeos/scripts/autonomy-heartbeat.py` before each material loop step, after each agent/work-package boundary, after each WO boundary, and at least every 30 minutes.
- Use `python3 ".vibeos/scripts/autonomy-loop.py" --project-dir "." --json` as the scheduler-safe one-tick entrypoint when an external scheduler or runtime adapter is driving the loop.
- Treat `.vibeos/autonomy/run-lease.json` as the active driver lease; `lease_conflict` means another loop or runtime adapter owns the run.
- Use `python3 ".vibeos/scripts/autonomy-runtime-adapter.py" --project-dir "." --json` to plan Codex/Claude runtime handoffs when the loop reports `handoff_required`; launch only with explicit `--execute`.
- Use `python3 ".vibeos/scripts/autonomy-failure-detector.py" --project-dir "." --json` when handoffs, runner blocks, lease conflicts, runtime failures, or provider/session limits repeat.
- Use `python3 ".vibeos/scripts/autonomy-recovery-planner.py" --project-dir "." --json` after blocking failure findings to produce the next safe plan-only response.
- Use `python3 ".vibeos/scripts/autonomy-recovery-resolution.py" --project-dir "." --action-id "<ACTION_ID>" --summary "<what changed>" --evidence "<path-or-note>" --json` to record evidence-backed resolution for recovery-plan actions.
- Use `python3 ".vibeos/scripts/autonomy-scheduler-guard.py" --project-dir "." --json` before scheduler-driven ticks; unresolved recovery actions without matching resolution evidence must block another tick.
- Use `python3 ".vibeos/scripts/autonomy-scheduler-profile.py" --project-dir "." --json` to generate scheduler profiles, and `python3 ".vibeos/scripts/autonomy-smoke.py" --runtime-provider codex --json` to smoke-test the chain before installation.
- Run `.vibeos/scripts/autonomy-supervisor.py` to write `.vibeos/autonomy/resume-plan.json` before choosing the next long-run action.
- Run `python3 ".vibeos/scripts/autonomy-runner.py" --project-dir "." --json` to classify the resume plan before acting on it.
- Use `python3 ".vibeos/scripts/autonomy-runner.py" --project-dir "." --execute --json` only for allowlisted local VibeOS script commands. Treat Codex/Claude continuation text as handoff-required work for the active runtime.
- Save `.vibeos/checkpoints/WO-*.json` at least every 60 minutes or after each agent/work-package boundary.
- Run checkpoint or session audit evidence at least every 180 minutes or phase boundary.
- Treat 24-48 hour autonomy as resumable execution. If the runtime is interrupted, resume from the latest heartbeat plus checkpoint.
- Run `.vibeos/scripts/validate-long-run-autonomy.py` before closeout. Session-end validation must pass with `--require-closed`.
- If `autonomy-failure-detector.py` reports repeated handoff, repeated no-progress decision, blocked runner, failed runtime launch, active lease conflict, or provider/session limit, pause autonomous scheduling and resolve the issue first.
- If `autonomy-recovery-planner.py` writes blocking actions, follow the plan and record `autonomy-recovery-resolution.py` evidence before another scheduler tick; do not auto-clear leases or launch providers unless explicitly reviewed.
- If `autonomy-scheduler-guard.py` blocks, do not run `autonomy-loop.py` again until the recovery plan has matching resolution evidence or is explicitly superseded.

## Codex Translation Rules

- Use Codex-native agents when `.vibeos/runtime-capabilities.json` and `.codex/agents/*.toml` show they are available. Otherwise read the matching `.codex/agent-contracts/*.md` template and perform that phase yourself.
- If `.claude/` is present, leave it intact. Shared runtime state lives in `.vibeos/`.
- If a gate or realistic verification path cannot run, report a truthful partial state instead of inventing completion.
