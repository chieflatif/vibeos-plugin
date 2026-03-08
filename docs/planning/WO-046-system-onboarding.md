# WO-046: System Onboarding & Concept Introduction

## Status

`Draft`

## Phase

Phase 7: Informed Onboarding & User Comprehension

## Objective

Create a first-time user experience that explains what VibeOS does, how it works, what the user's role is, and what to expect — before they enter the autonomous pipeline. Include a concept introduction system that explains terms on first use and a `/vibeos:help` skill for on-demand concept clarification.

## Scope

### In Scope
- [ ] First-run detection: identify when plugin is used for the first time on a project
- [ ] Onboarding message: 30-second plain English orientation on first use
- [ ] Explain the system: phases → WOs → agents → gates → audits → convergence
- [ ] Explain the user's role: decision maker, not code writer
- [ ] Explain what to expect: autonomous build with check-ins, not interactive coding
- [ ] Concept tracker: track which concepts have been introduced in the session
- [ ] First-use definitions: when a term is used for the first time, include inline definition
- [ ] Create `/vibeos:help` skill for on-demand concept clarification
- [ ] Update `skills/discover/SKILL.md` to include onboarding before discovery starts
- [ ] Store onboarding-complete flag in `.vibeos/config.json`

### Out of Scope
- Communication contract definition (WO-045)
- Build loop progress (WO-047)
- Decision support (WO-048)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-045 | User communication contract | Draft |

## Impact Analysis

- **Files created:** `skills/help/SKILL.md` (new skill)
- **Files modified:** `skills/discover/SKILL.md` (add onboarding), `.claude-plugin/plugin.json` (register help skill)
- **Systems affected:** Discovery flow, all skills (first-use definitions)

## Acceptance Criteria

- [ ] AC-1: First-run detection works (checks `.vibeos/config.json` for onboarding flag)
- [ ] AC-2: Onboarding message explains the system in under 200 words
- [ ] AC-3: User understands their role (decision maker, reviewer) vs system's role (builder, auditor)
- [ ] AC-4: User understands the flow (discover → plan → build → audit → repeat)
- [ ] AC-5: `/vibeos:help` skill created and answers concept questions
- [ ] AC-6: `/vibeos:help [term]` explains any glossary term from WO-045
- [ ] AC-7: `/vibeos:help` without arguments shows available topics
- [ ] AC-8: Onboarding skipped on subsequent runs (flag set)
- [ ] AC-9: User can re-trigger onboarding with `/vibeos:help onboarding`

## Test Strategy

- **First run:** Verify onboarding fires on first `/vibeos:discover` invocation
- **Subsequent run:** Verify onboarding skipped when flag is set
- **Help skill:** Verify `/vibeos:help` responds to glossary terms
- **Comprehension:** Review onboarding text for clarity with non-technical reader

## Implementation Plan

### Step 1: Create Onboarding Message
Before the first skill action, present:

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
> Let's start by understanding what you want to build.

### Step 2: First-Run Detection
In each skill, check at the start:
```
if .vibeos/config.json does not exist or onboarding_complete is false:
  present onboarding message
  set onboarding_complete: true
```

### Step 3: Create `/vibeos:help` Skill
`skills/help/SKILL.md`:
- If `$ARGUMENTS` is a glossary term: explain that term with examples
- If `$ARGUMENTS` is "onboarding": re-show the onboarding message
- If `$ARGUMENTS` is empty: show available topics
- Topics include: phases, work-orders, quality-gates, audit-agents, convergence, baselines, ratcheting, tdd, autonomy-levels, communication, and all glossary terms from WO-045

### Step 4: Update Discover Skill
Add onboarding check at the top of `skills/discover/SKILL.md`:
- Before "Tell me what you want to build", check if this is the first run
- If first run: show onboarding, then proceed
- If midstream (existing code): adjust onboarding to mention "I see you already have code — I'll start by understanding what's here"

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Review onboarding text for clarity, test help skill responses
- Risk: Onboarding must be brief enough not to annoy returning users, comprehensive enough for first-timers

## Evidence

- [ ] Onboarding fires on first use
- [ ] Onboarding skipped on subsequent use
- [ ] Help skill responds to all glossary terms
- [ ] Onboarding text is clear to non-technical reader
- [ ] Midstream variant mentions existing code
