---
name: vibeos-autonomous
description: Full autonomous-session override for VibeOS in Codex. Use when the user says go autonomous, stop checking in, run on your own, stay in autonomous mode, or wants VibeOS to keep building until a real blocker or decision appears.
---

# VibeOS Autonomous

Use this skill to turn on a temporary full-autonomous session override. For 24-48 hour work, treat autonomy as a resumable long-run protocol with heartbeat evidence, checkpoints, audit cadence, failure detection, recovery planning, evidence-backed recovery resolution, scheduler guarding, and explicit stop conditions.

## Workflow

1. Read or create `.vibeos/config.json`.
2. Preserve the negotiated autonomy level and set:
   - `autonomy.session_override.mode = "autonomous"`
   - `autonomy.session_override.active = true`
   - `autonomy.long_run.active = true`
   - `autonomy.long_run.target_hours = 24`
   - `autonomy.long_run.max_hours = 48`
   - `autonomy.long_run.heartbeat_interval_minutes = 30`
   - `autonomy.long_run.checkpoint_interval_minutes = 60`
   - `autonomy.long_run.audit_interval_minutes = 180`
3. Read or create `.vibeos/session-state.json` and mark the session active in autonomous mode with a `long_run` block.
4. Append a mode-change entry to `.vibeos/build-log.md`.
5. If available, record a heartbeat:
   ```bash
   python3 ".vibeos/scripts/autonomy-heartbeat.py" --status running --iteration 0 --summary "autonomous long-run session enabled" --next-action "continue build loop"
   python3 ".vibeos/scripts/autonomy-supervisor.py" --project-dir "."
   python3 ".vibeos/scripts/autonomy-runner.py" --project-dir "." --json
   python3 ".vibeos/scripts/autonomy-loop.py" --project-dir "." --json
   python3 ".vibeos/scripts/autonomy-runtime-adapter.py" --project-dir "." --json
   python3 ".vibeos/scripts/autonomy-failure-detector.py" --project-dir "." --json
   python3 ".vibeos/scripts/autonomy-recovery-planner.py" --project-dir "." --json
   python3 ".vibeos/scripts/autonomy-recovery-resolution.py" --project-dir "." --json
   python3 ".vibeos/scripts/autonomy-scheduler-guard.py" --project-dir "." --json
   python3 ".vibeos/scripts/autonomy-scheduler-profile.py" --project-dir "." --json
   python3 ".vibeos/scripts/autonomy-smoke.py" --runtime-provider codex --json
   ```
6. Explain what changes:
   - routine check-ins stop
   - 24-48 hour runs write resumable heartbeat, checkpoint, and audit evidence
   - gates and audit rules still apply
   - the system will still pause for blockers, risk decisions, or plan boundaries
7. Continue immediately with `vibeos-build`.

## Rules

- Keep the override truthful and explicit in state files.
- When autonomous mode ends, clear the override and record the session handoff.
- Use `autonomy-loop.py` for scheduler-safe loop ticks when a non-model process is driving the session.
- Respect `.vibeos/autonomy/run-lease.json`; a `lease_conflict` result means another autonomy driver is active.
- Use `autonomy-runtime-adapter.py` for dry-run-first Codex/Claude handoff planning; launch only with explicit `--execute`.
- Use `autonomy-failure-detector.py` for repeated handoff loops, runner blocks, runtime failures, lease conflicts, and provider/session limits.
- Use `autonomy-recovery-planner.py` for plan-only recovery actions after failure detection.
- Use `autonomy-recovery-resolution.py` to record summary and evidence for resolved recovery actions.
- Use `autonomy-scheduler-guard.py` to block scheduler-driven ticks while recovery actions lack matching resolution evidence.
- Use `autonomy-scheduler-profile.py` only to generate reviewed profile files.
- Use `autonomy-smoke.py` before trusting a generated scheduler profile.
- Record a heartbeat at least every 30 minutes, after each WO boundary, and after checkpoint/audit boundaries.
- Classify supervisor resume plans with `autonomy-runner.py`; use `--execute` only for allowlisted local VibeOS scripts.
- Save checkpoints at least every 60 minutes or after each agent/work-package boundary.
- Run checkpoint or session audit evidence at least every 180 minutes or phase boundary.
- Terminal long-run states must record `complete`, `paused`, or `blocked` through `autonomy-heartbeat.py`, then pass `validate-long-run-autonomy.py --require-closed`.
