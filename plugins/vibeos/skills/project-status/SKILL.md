---
name: project-status
description: Show a founder-style executive project status briefing. Use when the user asks "project status", "where are we overall?", "give me the big picture", "executive briefing", "founder update", "program status", or wants a strategic, evidence-based view of overall progress, risks, business impact, and decisions.
allowed-tools: Read, Glob, Grep
---

# /vibeos:project-status — Executive Project Briefing

Show a strategic, founder-friendly status briefing for the overall project or program.

## Instructions

1. **Read the strategic evidence base** (if it exists):
   - `project-definition.json` — machine-readable project definition
   - `docs/product/PROJECT-IDEA.md`, `docs/product/PRODUCT-BRIEF.md`, `docs/product/PRD.md` — product intent
   - `docs/product/PRODUCT-ANCHOR.md` — product promise and experience guardrails
   - `docs/ENGINEERING-PRINCIPLES.md` — quality bar and anti-shortcut rules
   - `docs/planning/DEVELOPMENT-PLAN.md` — phases and sequencing
   - `docs/planning/WO-INDEX.md` — work-order coverage and completion state
   - `.vibeos/findings-registry.json` — remediation backlog and accepted risks
   - `.vibeos/audit-reports/` and `.vibeos/session-audits/` — latest evidence of quality posture
   - `docs/research/RESEARCH-REGISTRY.md` — freshness of external technical decisions
   - `docs/decisions/DEVIATIONS.md` — explicit trade-offs and compromises
   - top-level README or architecture docs, if they help identify what is already working in the product

2. **Determine the overall program state**:
   - What stage is the project actually in, in plain English?
   - What user-visible or business-relevant progress is real and evidenced?
   - What remains unfinished before the product reaches the next meaningful milestone?
   - What risks, governance gaps, or quality debt could change the business outcome?
   - What decisions need founder input now?

3. **Translate technical progress into business meaning**:
   - Do not lead with WO numbers, issue IDs, or backlog bookkeeping
   - Explain what has been accomplished in terms of product capability, delivery readiness, and business impact
   - If evidence is weak or mixed, say so clearly instead of overstating confidence

4. **Report the executive briefing**:

   ```markdown
   ## Project Status

   **Bottom line:** [1-3 sentence executive summary]
   **Program stage:** [plain English stage]
   **Confidence:** [high / medium / low] — [why]
   **What this means for the business:** [plain English interpretation]

   ### Evidence-Based Progress
   - [major completed outcome]
   - [major completed outcome]
   - [what that progress means]

   ### What Still Needs To Happen
   - [major remaining milestone]
   - [critical unfinished area]
   - [important non-code work if relevant]

   ### Risks And Issues
   - [delivery risk]
   - [quality or governance risk]
   - [research freshness or dependency risk]

   ### Strategic Priorities
   1. [highest-leverage next priority]
   2. [second priority]
   3. [third priority]

   ### Decisions Needed From You
   - [decision, why it matters, and recommended direction]
   ```

5. **If the project is not yet fully set up**:
   - say so in plain English
   - explain whether the project is still in discovery, planning, remediation, or build setup
   - recommend the next best strategic step

## Communication Contract

Follow the full USER-COMMUNICATION-CONTRACT.md (`docs/USER-COMMUNICATION-CONTRACT.md`). Key rules:
- Lead with outcome, follow with mechanism
- Present decisions with consequences
- Introduce every concept on first use with plain English definition

Skill-specific addenda:
- This is an executive briefing, not a backlog dump
- Translate technical evidence into product, delivery, risk, and business meaning
- Avoid leading with WO numbers, ticket IDs, or raw audit counts unless the user explicitly asks for them
- If a choice is needed, present options with pros, cons, and a recommendation
