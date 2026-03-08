# WO-044: Remediation Roadmap & Phase 0 Enforcement

## Status

`Complete`

## Phase

Phase 7: Informed Onboarding & User Comprehension

## Objective

Create a proper remediation roadmap that integrates user-decided finding dispositions into the development plan. Phase 0 (remediation) is enforced — the build skill won't start feature work until Phase 0 findings are dispositioned and critical fix-now items are resolved. Fix-later items get tracked remediation WOs with deadlines. Accepted risks get documented justifications.

## Scope

### In Scope
- [x] Generate remediation roadmap from findings-registry.json dispositions
- [x] Phase 0 WOs created from `fix-now` findings (one WO per critical, grouped highs)
- [x] Parallel remediation track for `fix-later` items (WOs created but not blocking Phase 1)
- [x] Accepted risk register: `docs/planning/ACCEPTED-RISKS.md` with justifications
- [x] Phase 0 enforcement: build skill checks Phase 0 completion before starting Phase 1
- [x] User negotiation: which fix-later items go into Phase 0 vs parallel track
- [x] Remediation WO template variant: links to finding ID, includes verification criteria
- [x] Progress tracking: remediation items in `/vibeos:status` output
- [x] Periodic reminder: when fix-later items age beyond configurable threshold (default: 5 WOs)
- [x] Update `skills/plan/SKILL.md` to generate Phase 0 from findings
- [x] Update `skills/build/SKILL.md` Step 1 to enforce Phase 0 completion
- [x] Update `skills/status/SKILL.md` to show remediation status

### Out of Scope
- Running the audits (WO-042)
- Baseline model (WO-043)
- Automated fixing of findings

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-043 | Finding-level baseline | Complete |

## Impact Analysis

- **Files modified:** `skills/plan/SKILL.md` (Phase 0 generation — WO-044 is the **sole owner** of remediation WO creation, superseding the existing Step 1b remediation logic that WO-041 replaces), `skills/build/SKILL.md` (Phase 0 enforcement at Step 1, aging reminders after WO completion), `skills/status/SKILL.md` (remediation display). Note: Phase 0 enforcement reads `.vibeos/findings-registry.json` directly (via jq) to check fix-now completion status — no modifications to `convergence/baseline-check.sh` needed (WO-043 owns that file).
- **Files created:** `docs/planning/ACCEPTED-RISKS.md` (in target project), `docs/planning/REMEDIATION-ROADMAP.md` (in target project)
- **Systems affected:** Plan skill, build skill, status skill, WO creation
- **Note:** WO-047 also modifies `skills/build/SKILL.md` for progress reporting. WO-044 should be implemented first; WO-047 adds progress banners around WO-044's enforcement and reminder logic.

## Acceptance Criteria

- [x] AC-1: fix-now findings become Phase 0 WOs
- [x] AC-2: fix-later findings become tracked remediation WOs with priority
- [x] AC-3: accepted-risk findings documented in ACCEPTED-RISKS.md with justifications
- [x] AC-4: Build skill enforces Phase 0: won't start Phase 1 until fix-now items resolved
- [x] AC-5: User can negotiate which items go into Phase 0 vs parallel track
- [x] AC-6: Remediation WOs link to specific finding IDs from findings-registry.json
- [x] AC-7: Status skill shows remediation progress (N fix-now resolved, M fix-later remaining)
- [x] AC-8: Periodic reminder when fix-later items age beyond threshold (configurable in `.vibeos/config.json` as `remediation_aging_threshold`, default: 5 WOs)
- [x] AC-9: REMEDIATION-ROADMAP.md generated with timeline and dependencies
- [x] AC-10: Greenfield projects unaffected (no Phase 0 if no pre-existing findings)

## Test Strategy

- **Integration:** Run full midstream flow, verify Phase 0 created from fix-now items
- **Enforcement:** Try to start Phase 1 with incomplete Phase 0, verify blocked
- **Tracking:** Verify status skill shows remediation progress
- **Aging:** Verify reminder fires when fix-later items exceed threshold

## Implementation Plan

### Step 1: Generate Phase 0 from Findings
After guided audit (WO-042) and baseline creation (WO-043):
1. Read findings-registry.json
2. Group fix-now findings into WOs:
   - One WO per critical finding (high priority, specific scope)
   - Group related high findings into WOs (e.g., all auth issues in one WO)
3. Create fix-later WOs with lower priority
4. Write REMEDIATION-ROADMAP.md

### Step 2: Generate Accepted Risks Register
For accepted-risk findings:
- Write `docs/planning/ACCEPTED-RISKS.md`
- Each entry includes: finding ID, description, risk level, justification, date, reviewer
- This document is the audit trail for compliance (SOC 2, etc.)

### Step 3: Phase 0 Enforcement
Update `skills/build/SKILL.md` Step 1 (identify next WO):
- Before looking for feature WOs, check if Phase 0 exists and has incomplete items
- If Phase 0 has incomplete fix-now WOs: build those first
- If Phase 0 is complete or doesn't exist: proceed to Phase 1
- User can override with explicit "skip Phase 0" (logged as risk acceptance)

### Step 4: Remediation Progress in Status
Update `skills/status/SKILL.md`:
- Add "Remediation Status" section:
  > **Remediation Status:**
  > - Fix Now: [N] resolved / [M] total
  > - Fix Later: [N] resolved / [M] total ([K] overdue)
  > - Accepted Risks: [N] documented

### Step 5: Aging Reminders
In `skills/build/SKILL.md`, after each WO completion:
1. Check fix-later items in findings-registry.json
2. Count WOs completed since each item was baselined (using the `baselined_at_wo` field in findings-registry.json — set by WO-043 when the finding is first baselined)
3. Read threshold from `.vibeos/config.json` `remediation_aging_threshold` (default: 5 WOs)
4. If any item exceeds threshold:
   > "Reminder: [N] fix-later remediation items have been deferred for [M] work orders. Consider scheduling them soon:
   > - [finding summary] (deferred since WO-NNN)
   > Run `/vibeos:status` to see the full list."

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Test status: Integration test — midstream project with mixed dispositions
- Risk: Phase 0 enforcement could frustrate users who want to start feature work immediately; must clearly explain why and offer escape hatch

## Evidence

- [x] Phase 0 WOs created from fix-now findings
- [x] fix-later WOs created and tracked
- [x] Accepted risks documented with justifications
- [x] Phase 0 enforcement works
- [x] Status skill shows remediation progress
- [x] Aging reminders fire correctly
