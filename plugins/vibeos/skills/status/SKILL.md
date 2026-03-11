---
name: status
description: Show tactical session status for the current or most recent work session. Use when the user asks "what's the status?", "where are we in this session?", "remind me what we're doing", "what's in flight?", "what still needs doing right now?", or wants a micro-level update on the active work.
allowed-tools: Read, Glob, Grep
---

# /vibeos:status — Session Status

Show a tactical status briefing for the current or most recent VibeOS work session.

## Instructions

1. **Read the tactical session evidence** (if it exists):
   - `.vibeos/session-state.json` — active or most recent session record
   - `.vibeos/build-log.md` — recent execution history
   - `.vibeos/checkpoints/*.json` — in-progress resume state
   - `.vibeos/config.json` — autonomy preference and session override
   - `docs/planning/WO-INDEX.md` — active and recently completed work orders
   - active WO files (status `In Progress`, `Active`, `Implemented Locally`, `Awaiting Gate Cleanup`, `Awaiting Real-Path Verification`, `Dev-Mode Complete`, `Awaiting Checkpoint`, `Awaiting Evidence`, or `Pre-Commit Audit`)
   - the latest file in `.vibeos/session-audits/`, if present

2. **Determine current tactical state**:
   - Is there an active session, or only a recent one?
   - What is the current focus in plain English?
   - What has been completed in this session?
   - What is still in motion right now?
   - What blocker, failed check, or pending decision is slowing this session down?
   - Whether the active WO is in a truthful partial state such as `Implemented Locally`, `Awaiting Gate Cleanup`, `Awaiting Real-Path Verification`, `Dev-Mode Complete`, `Awaiting Checkpoint`, `Awaiting Evidence`, or `Pre-Commit Audit`

3. **Check tactical governance and quality signals**:
   - whether the autonomous session override is active
   - whether a checkpoint exists
   - whether the latest session audit found unresolved issues
   - whether the current or recent WOs show blocked status or unresolved acceptance criteria

4. **Report the session briefing**:

   ```markdown
   ## Session Status

   **Bottom line:** [1-2 sentence tactical summary]
   **Session state:** [active / paused / no active session]
   **Current focus:** [plain English description]
   **Mode:** [standard / autonomous override]

   ### Done In This Session
   - [plain English outcome]
   - [plain English outcome]

   ### Still In Motion
   - [current implementation or follow-up work]
   - [current verification or audit work]

   ### Issues Or Blockers
   - [none, or plain English blocker]
   - [risk, failed check, or missing decision]

   ### Next Tactical Move
   [What should happen next in this session]
   [Why that is the right immediate move]

   ### Decision Needed From You
   [Only if a decision is truly needed. Otherwise say "None right now."]
   ```

5. **If there is no active session**:
   - say that clearly
   - summarize the most recent session only if there is credible evidence
   - recommend asking for **project status** if the user wants the overall founder-level view

## Communication Contract

Follow the full USER-COMMUNICATION-CONTRACT.md (`docs/USER-COMMUNICATION-CONTRACT.md`). Key rules:
- Lead with outcome, follow with mechanism
- Present decisions with consequences
- Introduce every concept on first use with plain English definition

Skill-specific addenda:
- Keep this tactical and near-term, not strategic
- Avoid leading with WO numbers, issue IDs, or backlog references; translate them into plain English first
- If IDs help, put them after the plain English explanation, not before it
- If a choice is needed, present options with pros, cons, and a recommendation
