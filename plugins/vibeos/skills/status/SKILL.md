---
name: status
description: Show project dashboard with current phase, active work orders, recent audit results, and recommended next action. Use when the user asks "how's it going?", "what's the status?", "where are we?", "what's done?", "update me", or wants to see progress, what to work on next, or an overview of the project.
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

3. **Check remediation status** (if `.vibeos/findings-registry.json` exists):
   - Count fix-now findings and their resolution status
   - Count fix-later findings and how many are overdue
   - Count accepted-risk findings

4. **Report the dashboard**:

   ```
   ## Project Status

   **Phase:** [current phase name]
   **Active WOs:** [list or "none"]
   **Recently Completed:** [last 3 completed WOs]

   ## Remediation Status
   (only shown for midstream projects with findings)

   - **Fix Now:** [N] resolved / [M] total
   - **Fix Later:** [N] resolved / [M] total ([K] overdue)
   - **Accepted Risks:** [N] documented

   ## Next Recommended Action
   [What WO should be started next, based on dependency graph and phase ordering]
   [Why this is the right next step]
   [If Phase 0 has incomplete fix-now items, recommend those first]

   ## Blockers
   [Any blocked WOs with reason, or "None"]
   [If Phase 0 incomplete and user trying to start Phase 1, flag it]
   ```

5. **If no governance files exist**: Report that the project hasn't been set up with VibeOS governance yet, and suggest running `/vibeos:discover` to start.

## Communication Contract

Follow the full USER-COMMUNICATION-CONTRACT.md (`docs/USER-COMMUNICATION-CONTRACT.md`). Key rules:
- Lead with outcome, follow with mechanism
- Present decisions with consequences
- Introduce every concept on first use with plain English definition

Skill-specific addenda:
- Keep the output scannable — use tables and bullet points
- Flag blockers proactively
- Explain the recommended next step in plain English first; add technical detail only when it helps the user understand why
- If a choice is needed, present options with pros, cons, and a recommendation
