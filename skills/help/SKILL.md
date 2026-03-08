---
name: help
description: Get help with VibeOS concepts, glossary terms, and system orientation. Use to understand any term or concept used by the plugin, or to re-trigger the onboarding introduction.
argument-hint: "[topic or glossary term, e.g. 'work-orders', 'ratchet', 'onboarding']"
allowed-tools: Read, Glob, Grep
---

# /vibeos:help — Concept Help & Orientation

Explain VibeOS concepts, glossary terms, and system orientation on demand.

## Communication Contract

Follow the full USER-COMMUNICATION-CONTRACT.md (`${CLAUDE_PLUGIN_ROOT}/docs/USER-COMMUNICATION-CONTRACT.md`). Key rules:
- Lead with outcome, follow with mechanism
- Present decisions with consequences
- Introduce every concept on first use with plain English definition

**Skill-specific addenda:**
- Always explain terms in plain English first, then provide the technical detail
- Use examples from the user's project context when possible

## Help Flow

### If `$ARGUMENTS` is empty: Show Available Topics

> **VibeOS Help Topics**
>
> You can ask about any of these topics:
>
> **System Concepts:**
> - `phases` — How work is organized into milestones
> - `work-orders` — Detailed task specifications
> - `quality-gates` — Automated quality checks
> - `audit-agents` — Specialized code reviewers
> - `convergence` — How the build loop reaches completion
> - `baselines` — Quality snapshots and tracking
> - `ratcheting` — One-way quality improvement
> - `tdd` — Test-driven development approach
> - `autonomy-levels` — How much control you retain
> - `layers` — The 7-layer quality enforcement system
>
> **Glossary Terms:**
> - `wo`, `phase`, `gate`, `gate-runner`, `consensus`, `finding`, `disposition`, `phase-0`, `midstream`, `check-in`
>
> **Other:**
> - `files` — What files the plugin creates in your project
> - `onboarding` — Re-show the system introduction
> - `communication` — How the system communicates with you
>
> Example: `/vibeos:help ratcheting`

### If `$ARGUMENTS` is "onboarding": Show System Introduction

> **Welcome to VibeOS**
>
> VibeOS turns Claude into an autonomous development engine. Here's how it works:
>
> 1. **You describe what you want to build** — I'll ask questions to understand your vision
> 2. **I create a development plan** — broken into phases and work orders (detailed task specs)
> 3. **I build autonomously** — writing tests first, then code, with quality checks at every step
> 4. **I check in with you** — at natural pause points so you can review, redirect, or continue
>
> **Your role:** You make the decisions — what to build, what quality level to target, when to ship. I handle the implementation, testing, and quality enforcement.
>
> **What to expect:** You'll see progress updates as each piece is built. I'll explain what I'm doing in plain English. When I need your input, I'll present clear options with their implications.
>
> **Key commands:**
> - `/vibeos:discover` — Start a new project or analyze existing code
> - `/vibeos:plan` — Generate a development plan
> - `/vibeos:build` — Start or continue building
> - `/vibeos:status` — See current progress
> - `/vibeos:help [topic]` — Learn about any concept

### If `$ARGUMENTS` is a glossary term or topic: Explain It

Read the glossary from `${CLAUDE_PLUGIN_ROOT}/docs/USER-COMMUNICATION-CONTRACT.md` and provide the definition along with:
1. A plain English explanation
2. Why it matters to the user
3. An example from a typical project

**Topic explanations:**

- **phases**: "A phase is a group of related work orders that together deliver a milestone. Phase 1 is usually Foundation (project scaffolding, database, auth). Later phases deliver features. You'll review at the end of each phase."

- **work-orders**: "A work order (WO) is a detailed specification for one unit of work — like a task card with acceptance criteria, dependencies, and a test plan. The build system executes one WO at a time."

- **quality-gates**: "Quality gates are automated checks that run before code is committed. They catch issues like missing type annotations, placeholder code, security vulnerabilities, and style violations. Think of them as a safety inspection."

- **audit-agents**: "Audit agents are specialized AI reviewers that examine your code for specific types of issues. There are 5: security, architecture, correctness, test coverage, and evidence. They run independently and their findings are cross-referenced for consensus."

- **convergence**: "Convergence is the process of fix cycles getting closer to zero issues. After the build agent writes code, auditors review it, and any issues trigger a fix cycle. Convergence controls prevent infinite loops by tracking whether progress is being made."

- **baselines**: "A baseline is a snapshot of your codebase's current quality level — the starting point. For new projects, the baseline is zero issues. For existing codebases (midstream), the baseline captures pre-existing issues so they don't block new work."

- **ratcheting**: "A ratchet is a rule that quality can only improve, never get worse. Once you fix an issue, the system won't allow that type of issue to be reintroduced. Like a one-way valve for code quality."

- **tdd**: "Test-Driven Development means tests are written before code. The tester agent writes tests from the work order spec (never seeing the implementation), then the implementation agent writes code to make those tests pass. This ensures tests reflect requirements, not implementation."

- **autonomy-levels**: "Autonomy levels control how often the system checks in with you. Level 'wo' pauses after every work order. Level 'phase' pauses after each phase (recommended). Level 'major' only pauses for important decisions."

- **layers**: "The quality enforcement system has 7 layers: L0 (hooks — real-time), L1 (gate scripts — pre-commit), L2 (audit agents — post-implementation), L3 (convergence — loop control), L4 (consensus — cross-agent verification), L5 (phase boundary — milestone check), L6 (human check-in — your review)."

- **disposition**: "A disposition is your decision about what to do with a finding: 'fix-now' (must fix before starting feature work), 'fix-later' (tracked, reminded periodically), or 'accepted-risk' (documented with your justification)."

- **phase-0**: "Phase 0 is the remediation phase for existing codebases. It contains work orders to fix critical issues found during the initial audit. Phase 0 must be completed before feature work (Phase 1+) begins."

- **midstream**: "Midstream means the plugin is being added to a project that already has code. The system analyzes the existing codebase, maps its architecture, runs audits, and creates a baseline before planning new work."

- **files**: "The plugin creates files in your project at different stages. Here's a summary by phase:"
  - **Discovery:** `project-definition.json`, product docs in `docs/product/` (PRD, architecture, tech spec)
  - **Planning:** `DEVELOPMENT-PLAN.md` and work orders in `docs/planning/`, gate scripts in `scripts/`, `CLAUDE.md`
  - **Midstream planning:** `.vibeos/findings-registry.json` (audit findings), `.vibeos/baselines/` (quality baseline), `ACCEPTED-RISKS.md`
  - **Build:** Source code, test files, `.vibeos/build-log.md` (build history), `.vibeos/checkpoints/` (resume state)
  - "All plugin state lives in the `.vibeos/` directory. For the full list, see `docs/FILE-INVENTORY.md` or run `/vibeos:help files`."

For any term not listed above, read the glossary in `${CLAUDE_PLUGIN_ROOT}/docs/USER-COMMUNICATION-CONTRACT.md` and explain it with the same pattern: plain English definition, why it matters, example.
