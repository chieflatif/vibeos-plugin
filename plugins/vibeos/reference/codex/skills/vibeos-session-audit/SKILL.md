---
name: vibeos-session-audit
description: Closeout audit for the current or most recent VibeOS build session in Codex. Use when the user says audit this session, review this run, session audit, or wants a trustworthy end-to-end review of what happened in the latest build session.
---

# VibeOS Session Audit

Use this skill to audit the current or most recent build session.

## Workflow

1. Read:
   - `.vibeos/build-log.md`
   - `.vibeos/session-state.json`
   - `.vibeos/autonomy/heartbeats/*.json`
   - `.vibeos/autonomy/run-lease.json`
   - `.vibeos/autonomy/last-lease.json`
   - `.vibeos/autonomy/lease-conflict.json`
   - `.vibeos/autonomy/loop-state.json`
   - `.vibeos/autonomy/loop-history.jsonl`
   - `.vibeos/autonomy/resume-plan.json`
   - `.vibeos/autonomy/runner-report.json`
   - `.vibeos/autonomy/runtime-adapter-plan.json`
   - `.vibeos/autonomy/runtime-adapter-history.jsonl`
   - `.vibeos/autonomy/failure-report.json`
   - `.vibeos/autonomy/recovery-plan.json`
   - `.vibeos/autonomy/recovery-resolution.json`
   - `.vibeos/autonomy/recovery-resolution-history.jsonl`
   - `.vibeos/autonomy/scheduler-guard-report.json`
   - `.vibeos/autonomy/scheduler-profile.json`
   - `.vibeos/autonomy/smoke-report.json`
   - `docs/planning/DEVELOPMENT-PLAN.md`
   - `docs/planning/WO-INDEX.md`
   - WO files touched in the session
2. Re-run session-closeout verification:

```bash
bash ".vibeos/scripts/gate-runner.sh" pre_commit --continue-on-failure
bash ".vibeos/scripts/gate-runner.sh" session_end --continue-on-failure
python3 ".vibeos/scripts/validate-long-run-autonomy.py" --project-dir "." --require-closed
python3 ".vibeos/scripts/autonomy-failure-detector.py" --project-dir "." --json
python3 ".vibeos/scripts/autonomy-recovery-planner.py" --project-dir "." --json
python3 ".vibeos/scripts/autonomy-recovery-resolution.py" --project-dir "." --json
python3 ".vibeos/scripts/autonomy-scheduler-guard.py" --project-dir "." --json
```

3. Include long-run autonomy status when heartbeat evidence exists: run id, latest heartbeat, active lease owner, last lease release, lease conflict evidence, loop iteration, loop tick status, checkpoint cadence, audit cadence, latest resume-plan decision, runner status, blocked commands, handoff-required items, runtime adapter provider/execution status, failure detector status/findings, recovery planner status/actions, recovery resolution status/evidence, scheduler guard status, scheduler profile status, smoke-test status, terminal state, and stop reason.
4. Use Codex-native auditors when available; otherwise use `.codex/agent-contracts/*auditor*.md` as role contracts and perform the audit phases yourself. Include dependency intelligence review when the session changed manifests, lockfiles, package managers, runtimes, SDKs, frameworks, or high-impact packages. Include delivery infrastructure review when the session changed CI/CD, deployment, environment/secrets, observability, health/smoke checks, rollback, runbooks, or operational scripts.
5. Save the report to `.vibeos/session-audits/` when the project uses that directory.
6. Separate what was completed from what still needs follow-up.

## Rules

- Never invent session evidence.
- If the session must be inferred from logs, say that explicitly.
- Close with a recommendation: continue, fix follow-ups first, or run a checkpoint.
