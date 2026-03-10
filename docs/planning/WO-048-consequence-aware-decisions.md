# WO-048: Consequence-Aware Decision Support

## Status

`Complete`

## Phase

Phase 7: Informed Onboarding & User Comprehension

## Objective

Every time the system presents the user with a choice, it includes the consequences of each option in plain English. No option is presented without the user understanding what will happen if they choose it. This applies to escalations, autonomy choices, gate skipping, finding dispositions, and all other decision points.

## Scope

### In Scope
- [x] Audit every decision point in all skills and identify missing consequence descriptions
- [x] Gate escalation: explain what each gate checks and what skipping means
- [x] Audit escalation: explain what each finding means and what accepting means
- [x] Autonomy selection: explain what each level means in practice (not just definition)
- [x] Finding disposition: explain what fix-now/fix-later/accepted-risk means concretely
- [x] Check-in options: explain what each choice leads to
- [x] Phase 0 skip: explain what deferring remediation means for code quality and security
- [x] Update all decision points in `skills/build/SKILL.md`
- [x] Update all decision points in `skills/plan/SKILL.md`
- [x] Update all decision points in `skills/audit/SKILL.md`
- [x] Update check-in report in `skills/build/SKILL.md` Step 11e
- [x] Define decision presentation template in Communication Contract

### Out of Scope
- Communication contract creation (WO-045)
- New decision points (only improving existing ones)
- Automated decision-making

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-045 | User communication contract | Complete |
| WO-044 | Remediation roadmap (soft) | Complete |
| WO-042 | Guided codebase audit (soft) | Complete |

**Soft dependency notes:**
- WO-044 creates the Phase 0 skip decision point. If WO-044 is not implemented when WO-048 runs, the Phase 0 skip item (scope line 24) should be marked as conditional and implemented when Phase 0 enforcement exists.
- WO-042 creates the finding disposition decision points (fix-now/fix-later/accepted-risk). WO-048 should audit and improve those decision points for consequence completeness.

## Impact Analysis

- **Files modified:** `skills/build/SKILL.md` (all escalation/decision points), `skills/plan/SKILL.md` (autonomy, intake, guided audit finding dispositions from WO-042), `skills/audit/SKILL.md` (finding review), `skills/discover/SKILL.md` (intent confirmation, gate failure decisions), `skills/checkpoint/SKILL.md` (ratchet violation decisions), `docs/USER-COMMUNICATION-CONTRACT.md` (decision template variant conforming to WO-045 schema)
- **Systems affected:** All user-facing decision points across all skills
- **Note:** WO-047 also modifies `skills/build/SKILL.md`. Both WOs should be implemented after Track A completes its modifications to avoid merge conflicts. WO-048 improves decision points including those created by WO-042 (finding dispositions) and WO-044 (Phase 0 skip).

## Acceptance Criteria

- [x] AC-1: Every decision point in build skill includes consequences for each option
- [x] AC-2: Gate skip option explains what quality checks are bypassed
- [x] AC-3: Audit accept option explains specific risks being accepted
- [x] AC-4: Autonomy options explain practical experience (not just abstract definition)
- [x] AC-5: Finding dispositions explain what happens for each choice
- [x] AC-6: Phase 0 skip option explains security/quality implications
- [x] AC-7: No decision point presents options as bare labels (a/b/c without context)
- [x] AC-8: Recommendations include reasoning, not just "I recommend X"
- [x] AC-9: Decision presentation follows Communication Contract template

## Test Strategy

- **Review:** Audit every AskUserQuestion and decision point in all skills
- **Consequence check:** For each option, verify a non-technical user would understand the impact
- **Bare label check:** Search for any remaining a/b/c options without consequence text

## Implementation Plan

### Step 1: Inventory All Decision Points
Audit all skills for decision points:

**Build skill (`skills/build/SKILL.md`):**
1. Gate failure escalation (3 cycles exhausted) — lines 166-167
2. Audit finding escalation (STUCK/MAX_ITER) — lines 222-230
3. Human check-in (5 options) — lines 334-339
4. Error recovery (agent timeout/garbage output) — lines 356-374

**Plan skill (`skills/plan/SKILL.md`):**
5. Autonomy negotiation (3 levels) — lines 338-366
6. Intake confirmations (18 questions) — lines 105-164
7. Solo compliance warning — lines 155-156
8. Plan validation ("Does this look correct?") — lines 177-180

**Audit skill (`skills/audit/SKILL.md`):**
9. Finding review (currently no decision point — should there be one?)

**Discover skill (`skills/discover/SKILL.md`):**
10. Intent confirmation ("Does this match your intent, or should I adjust anything?") — Step 2
11. Gate failure during discovery — Step 6

**Checkpoint skill (`skills/checkpoint/SKILL.md`):**
12. Ratchet violation response (what to do about quality regressions)

**Guided audit (WO-042, in `skills/plan/SKILL.md`):**
13. Per-finding disposition (fix-now/fix-later/accepted-risk) — if WO-042 is complete
14. Phase 0 negotiation (which fix-later items to escalate) — if WO-044 is complete

### Step 2: Rewrite Each Decision Point

**Gate failure escalation (current):**
> "Would you like me to: (a) try again with a different approach, (b) skip these gates for now, or (c) let you fix it manually?"

**Gate failure escalation (improved):**
> "Quality checks are still failing after 3 attempts. Here's what's failing: [specific issues].
>
> Your options:
> 1. **Try a different approach**
>    - Pros: best chance of resolving the issue without your manual work
>    - Cons: uses more time and tokens and may still fail
> 2. **Skip these checks for now**
>    - Pros: fastest path to continuing the build
>    - Cons: [specific risk, e.g., "type annotations won't be verified, which could let type-related bugs through"] remains until the checks are revisited
> 3. **Fix it yourself**
>    - Pros: gives you direct control over the exact remediation
>    - Cons: requires manual effort from you before the build can continue cleanly
>
> I recommend option 1 because [reason]."

**Audit escalation (legacy/problematic):**
> "The older version only asked the user to pick between shorthand choices without explaining the consequences or giving a recommendation."

**Audit escalation (improved):**
> "After [N] fix attempts, these issues remain:
> - [finding 1 with severity and file]
> - [finding 2 with severity and file]
>
> Your options:
> 1. **Try a different approach**
>    - Pros: best chance of clearing the findings without leaving risk behind
>    - Cons: uses more time and may still not resolve everything
> 2. **Accept these findings**
>    - Pros: preserves momentum on the current work
>    - Cons: [If security]: [specific security risk] remains in your code. [If architecture]: [specific maintenance risk] remains and may resurface later
> 3. **Fix it yourself**
>    - Pros: gives you full control over the remediation
>    - Cons: requires manual intervention before the issues are cleared
>
> I recommend [X] because [reason]."

### Step 3: Add Consequence Descriptions to Autonomy Options
The current autonomy options are already well-written. Enhance with practical examples:

> **Option A — Stop after every work order:**
> "I'll build one thing at a time and check in after each piece. For example, after building your user authentication, I'll show you what was built, what tests pass, and ask before moving to the next feature. **You'll review about [N] check-ins for this project.** Best if this is your first time using VibeOS or you want to stay closely involved."

### Step 4: Define Decision Template
Add to Communication Contract:
```
DECISION_TEMPLATE:
"[Context — what happened and why a decision is needed]

Your options:
1. **[Option name]**
   - Pros: [benefit]
   - Cons: [tradeoff]
   - Technical note: [optional technical detail when useful]
2. **[Option name]**
   - Pros: [benefit]
   - Cons: [tradeoff]
   - Technical note: [optional technical detail when useful]
3. **[Option name]**
   - Pros: [benefit]
   - Cons: [tradeoff]
   - Technical note: [optional technical detail when useful]

I recommend [option] because [specific reasoning based on project context]."
```

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Test status: Review every decision point in all skills for consequence completeness
- Risk: Overly verbose consequence descriptions could slow down experienced users; keep them concise

## Evidence

- [x] All decision points have consequence descriptions
- [x] Decision options include clear pros, cons, and a recommendation
- [x] No bare label options remain
- [x] Gate skip consequences explain specific risks
- [x] Audit accept consequences explain specific implications
- [x] Recommendations include reasoning
- [x] Non-technical user can understand every option
