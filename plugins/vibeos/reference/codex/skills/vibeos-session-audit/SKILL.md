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
   - `docs/planning/DEVELOPMENT-PLAN.md`
   - `docs/planning/WO-INDEX.md`
   - WO files touched in the session
2. Re-run session-closeout verification:

```bash
bash ".vibeos/scripts/gate-runner.sh" pre_commit --continue-on-failure
bash ".vibeos/scripts/gate-runner.sh" session_end --continue-on-failure
```

3. Use `.codex/agents/*auditor*.md` as role contracts and perform the audit phases yourself.
4. Save the report to `.vibeos/session-audits/` when the project uses that directory.
5. Separate what was completed from what still needs follow-up.

## Rules

- Never invent session evidence.
- If the session must be inferred from logs, say that explicitly.
- Close with a recommendation: continue, fix follow-ups first, or run a checkpoint.
