---
name: wo
description: Work order management with subcommands for creating, checking status, completing, and auditing individual work orders.
argument-hint: "<create|status|complete|audit> [WO number or title]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion
---

# /vibeos:wo — Work Order Management

Manage individual work orders: create new ones, check status, mark complete, or run audits.

## Communication Contract

Throughout this entire flow:
- Lead with the answer, not the reasoning
- Use the real term and explain it in plain language
- When presenting WO status, include what matters: what's done, what's blocked, what's next

## Subcommand Routing

Parse the first word of `$ARGUMENTS` to determine the subcommand:

- `create` — Create a new work order
- `status` — Show status of a specific WO (or current WO if none specified)
- `complete` — Mark a WO as complete with evidence validation
- `audit` — Run the plan auditor against a specific WO

If no subcommand is recognized, show help:
> "Usage: /vibeos:wo <create|status|complete|audit> [WO number]
>
> - **create** — Create a new work order from template
> - **status** — Show WO status, progress, and blockers
> - **complete** — Validate evidence and mark WO complete
> - **audit** — Run plan auditor against a WO"

---

## Subcommand: create

Create a new work order from the WO template.

1. Read `${CLAUDE_SKILL_DIR}/../../reference/governance/WO-TEMPLATE.md.ref` for the template structure
2. Read `docs/planning/WO-INDEX.md` to determine the next WO number
3. Ask the user for:
   - Title (required)
   - Objective (required)
   - Phase (which phase does this belong to)
   - Dependencies (other WO numbers)
   - Brief scope description
4. Generate the WO file at `docs/planning/WO-{NUMBER}-{slug}.md`:
   - Fill in all required sections from template
   - Set status to `Draft`
   - Set all acceptance criteria as unchecked
5. Add the new WO to `docs/planning/WO-INDEX.md` in the correct phase
6. Add the new WO to `docs/planning/DEVELOPMENT-PLAN.md` in the correct phase table

Report:
> "Created WO-{NUMBER}: {title}. Added to Phase {N} in the development plan."

---

## Subcommand: status

Show the status of a specific WO or the current active WO.

1. If a WO number is provided in `$ARGUMENTS`, use it
2. If not, read `docs/planning/DEVELOPMENT-PLAN.md` and find the first incomplete WO
3. Read the WO file
4. Read `docs/planning/WO-INDEX.md` for cross-reference

Report:
```
## WO-{NUMBER}: {title}

**Status:** {status}
**Phase:** {phase}
**Dependencies:** {list with status of each}

### Progress
- Scope items: {checked}/{total}
- Acceptance criteria: {checked}/{total}
- Evidence: {checked}/{total}

### Blockers
{list of blockers, or "None"}

### Next Step
{what should happen next}
```

---

## Subcommand: complete

Validate evidence and mark a WO as complete.

1. Read the WO file
2. **Validate all acceptance criteria have evidence:**
   - Each AC should be checked (`[x]`)
   - Each evidence item should be checked
   - If any are unchecked: report what's missing and ask the user to confirm
3. **Run pre-commit audit** using the 10-question framework:
   - What did we miss?
   - What tests are passing/failing?
   - Any remaining stubs or placeholders?
   - Should an additional audit run before marking complete?
4. **Run wo_exit gates** if gate-runner is available:
   ```bash
   bash scripts/gate-runner.sh wo_exit --continue-on-failure --wo {NUMBER}
   ```
5. **If all checks pass:**
   - Update WO status to `Complete`
   - Check all scope/AC/evidence boxes
   - Update `docs/planning/WO-INDEX.md` — move to Completed
   - Update `docs/planning/DEVELOPMENT-PLAN.md` — mark Complete
   - Report completion with summary
6. **If checks fail:**
   - Report what's failing
   - Ask: "Would you like to fix these first, or mark complete with noted exceptions?"

Report:
> "WO-{NUMBER} ({title}) is now Complete.
> - {N} acceptance criteria satisfied
> - {M} gates passed
> - Next: WO-{NEXT} ({next title})"

---

## Subcommand: audit

Run the plan auditor against a specific WO.

1. If a WO number is provided, use it
2. If not, use the current active WO
3. Dispatch `agents/plan-auditor.md` with the WO number
4. Present the structured findings to the user

Report the auditor's findings as-is, then add:
> "Would you like to address any of these findings before proceeding?"

---

## Output Summary

| Subcommand | Output |
|---|---|
| create | New WO file + updated WO-INDEX + updated DEVELOPMENT-PLAN |
| status | WO status report with progress and blockers |
| complete | WO marked complete + tracking docs updated |
| audit | Plan auditor findings |
