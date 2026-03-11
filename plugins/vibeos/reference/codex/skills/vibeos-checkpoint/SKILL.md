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
bash ".vibeos/scripts/gate-runner.sh" pre_commit --continue-on-failure
bash ".vibeos/scripts/gate-runner.sh" full_audit --continue-on-failure
```

3. Use `.codex/agents/*auditor*.md` as role contracts and execute the checkpoint review yourself.
4. Compare current quality posture against the previous baseline when `.vibeos/baselines/` exists.
5. Report whether quality held, improved, or regressed, and recommend the next move.

## Rules

- Explain ratchet failures in plain English.
- Do not move to the next phase silently when quality regressed.
- Store new checkpoint evidence when the project already uses baseline files.
