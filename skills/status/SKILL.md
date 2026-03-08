---
name: status
description: Show project dashboard with current phase, active work orders, recent audit results, and recommended next action. Use when the user asks about project status, progress, or what to work on next.
allowed-tools: Read, Glob, Grep
---

# /vibeos:status — Project Dashboard

Show a comprehensive project status overview.

## Instructions

1. **Read project governance files** (if they exist in the current project):
   - `docs/planning/DEVELOPMENT-PLAN.md` — phases and WO assignments
   - `docs/planning/WO-INDEX.md` — WO statuses and dependencies
   - Active WO files (any with status `In Progress` or `Active`)

2. **Determine current state**:
   - Which phase is the project in? (based on WO completion status)
   - Which WOs are active, blocked, or recently completed?
   - What dependencies are unblocked and ready to start?

3. **Report the dashboard**:

   ```
   ## Project Status

   **Phase:** [current phase name]
   **Active WOs:** [list or "none"]
   **Recently Completed:** [last 3 completed WOs]

   ## Next Recommended Action
   [What WO should be started next, based on dependency graph and phase ordering]
   [Why this is the right next step]

   ## Blockers
   [Any blocked WOs with reason, or "None"]
   ```

4. **If no governance files exist**: Report that the project hasn't been set up with VibeOS governance yet, and suggest running `/vibeos:discover` to start.

## Communication Contract

Follow the full USER-COMMUNICATION-CONTRACT.md (`${CLAUDE_PLUGIN_ROOT}/docs/USER-COMMUNICATION-CONTRACT.md`). Key rules:
- Lead with outcome, follow with mechanism
- Present decisions with consequences
- Introduce every concept on first use with plain English definition

Skill-specific addenda:
- Keep the output scannable — use tables and bullet points
- Flag blockers proactively
