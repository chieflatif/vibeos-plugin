---
name: vibeos-checkpoint
description: Phase-boundary checkpoint and ratchet review for VibeOS in Codex. Use when the user says phase is done, milestone check, checkpoint this phase, or wants a boundary audit before starting the next phase.
---

# VibeOS Checkpoint

Use this skill at phase boundaries.

## Workflow

1. Read `docs/planning/DEVELOPMENT-PLAN.md` and determine the target phase.
2. Run the shared gate suite:

```bash
if grep -q '"long_run"' ".vibeos/config.json" 2>/dev/null; then
  python3 ".vibeos/scripts/autonomy-heartbeat.py" --status checkpoint --summary "phase checkpoint started" --next-action "run full checkpoint gates and audits"
fi
bash ".vibeos/scripts/gate-runner.sh" pre_commit --continue-on-failure
bash ".vibeos/scripts/gate-runner.sh" full_audit --continue-on-failure
```

3. Use Codex-native auditors when available; otherwise use `.codex/agent-contracts/*auditor*.md` as role contracts and execute the checkpoint review yourself. Include dependency intelligence review for any phase that changed manifests, lockfiles, package managers, runtimes, SDKs, frameworks, or high-impact packages. Include delivery infrastructure review for any phase that changed CI/CD, deployment, environment/secrets, observability, health/smoke checks, rollback, runbooks, or operational scripts.
4. Compare current quality posture against the previous baseline when `.vibeos/baselines/` exists.
5. Report whether quality held, improved, or regressed, and recommend the next move.

## Rules

- Explain ratchet failures in plain English.
- Do not move to the next phase silently when quality regressed.
- Store new checkpoint evidence when the project already uses baseline files.
