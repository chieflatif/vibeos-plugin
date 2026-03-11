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
2. Determine the active WO and whether a checkpoint already exists.
3. Run the build phases yourself, using `.codex/agents/*.md` as role contracts:
   - `investigator.md`
   - `tester.md`
   - `prompt-engineer.md` when prompts or instruction assets change
   - `backend.md` and/or `frontend.md`
   - `doc-writer.md`
   - focused auditors when a WO needs extra scrutiny
4. Maintain truthful state in:
   - `.vibeos/build-log.md`
   - `.vibeos/checkpoints/WO-*.json`
   - `.vibeos/session-state.json`
5. Run shared gates:
   - `bash ".vibeos/scripts/gate-runner.sh" pre_commit --continue-on-failure`
   - `bash ".vibeos/scripts/gate-runner.sh" wo_exit --continue-on-failure` before true WO closeout
6. Only mark a WO `Complete` when behavior, real-path verification, relevant tests, and blocking gates are all evidenced.
7. If the user wants no routine check-ins, use `vibeos-autonomous`.

## Codex Translation Rules

- Do not assume executable subagents. Read the matching `.codex/agents/*.md` template and perform that phase yourself.
- If `.claude/` is present, leave it intact. Shared runtime state lives in `.vibeos/`.
- If a gate or realistic verification path cannot run, report a truthful partial state instead of inventing completion.
