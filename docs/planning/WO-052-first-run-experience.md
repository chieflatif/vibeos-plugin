# WO-052: First-Run Experience & Handoffs

## Status

`Complete`

## Phase

Phase 8: Resilience & Transparency

## Objective

Make the plugin's first impression clear and welcoming: users know what to do after installing, skills hand off to each other with context about what comes next, and users can see exactly what files the plugin creates in their project.

## Scope

### In Scope
- [x] SessionStart hook suggests first command: "Try `/vibeos:discover` to get started, or `/vibeos:help` to learn how VibeOS works"
- [x] README.md Quick Start section with recommended workflow (greenfield and midstream)
- [x] Discover → Plan handoff: replace generic "run /vibeos:plan" with specific preview of what plan will do
- [x] Plan → Build handoff: replace generic "run /vibeos:build" with preview of first WO
- [x] File creation inventory: document all files the plugin creates, organized by phase
- [x] Add file inventory to `/vibeos:help` as a topic ("files" or "project-files")
- [x] Midstream discovery handoff mentions guided audit will happen during planning

### Out of Scope
- Changing SessionStart hook to be blocking (remains informational)
- Creating a separate getting-started skill
- Interactive setup wizard

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| Phase 7 | All Phase 7 WOs | Complete |

## Impact Analysis

- **Files modified:** `hooks/scripts/prereq-check.sh` (add first-command suggestion), `README.md` (add Quick Start), `skills/discover/SKILL.md` (improve plan handoff), `skills/plan/SKILL.md` (improve build handoff), `skills/help/SKILL.md` (add file inventory topic)
- **Files created:** `docs/FILE-INVENTORY.md` (reference document listing all plugin-created files)
- **Systems affected:** First-run experience, skill-to-skill handoffs

## Acceptance Criteria

- [x] AC-1: SessionStart hook output includes suggestion to try `/vibeos:discover` or `/vibeos:help`
- [x] AC-2: README.md has Quick Start section with step-by-step for greenfield and midstream
- [x] AC-3: Discover skill's completion message previews what plan will do (not just "run /vibeos:plan")
- [x] AC-4: Plan skill's completion message previews the first WO and what build will do
- [x] AC-5: File inventory document exists listing all plugin-created files by phase
- [x] AC-6: `/vibeos:help files` shows what files the plugin creates and why
- [x] AC-7: Midstream discover handoff mentions guided audit happens during planning
- [x] AC-8: All handoff messages follow Communication Contract patterns

## Test Strategy

- **First run:** Install plugin on clean project, verify SessionStart suggests next steps
- **README:** Review Quick Start for clarity with non-technical audience
- **Handoffs:** Run discover → plan → build, verify each handoff previews next step
- **Inventory:** Compare file inventory against actual files created during full flow

## Implementation Plan

### Step 1: Enhance SessionStart Hook
Update `hooks/scripts/prereq-check.sh` output message:
- Current: "VibeOS Plugin: All prerequisites available..."
- New: "VibeOS Plugin: All prerequisites available. Try `/vibeos:discover` to get started with a new project, or `/vibeos:help` to learn how VibeOS works."
- If midstream indicators detected (existing source files): "VibeOS Plugin: All prerequisites available. I see existing code — `/vibeos:discover` will analyze your codebase before planning. Try `/vibeos:help` for an overview."

### Step 2: Add Quick Start to README.md
```markdown
## Quick Start

### New Project
1. `/vibeos:discover` — Describe what you want to build. I'll ask questions and create product docs.
2. `/vibeos:plan` — I'll generate a phased development plan with work orders.
3. `/vibeos:build` — I'll build autonomously, checking in at natural pause points.

### Existing Project
1. `/vibeos:discover` — I'll analyze your codebase and create architecture docs.
2. `/vibeos:plan` — I'll audit your code for issues and create a remediation + feature plan.
3. `/vibeos:build` — Critical issues first (Phase 0), then feature work.

### Anytime
- `/vibeos:status` — See where things stand
- `/vibeos:help` — Learn any concept
- `/vibeos:gate` — Run quality checks manually
```

### Step 3: Improve Discover → Plan Handoff
Replace generic "Run `/vibeos:plan`" with:

**Greenfield:**
> "Discovery is complete. Next step: `/vibeos:plan` — I'll ask about your technical preferences (framework, database, deployment), configure quality gates for your project, and generate a phased development plan with specific work orders. This usually takes 5-10 minutes of your input."

**Midstream:**
> "Discovery is complete. Next step: `/vibeos:plan` — I'll run a guided audit of your codebase, walk you through any issues I find (you'll decide what to fix now vs later), then generate a development plan. The audit covers security, architecture, code quality, dependencies, and test coverage."

### Step 4: Improve Plan → Build Handoff
Replace generic "Run `/vibeos:build`" with:
> "Planning is complete. Your first work order is WO-[NNN]: [title] — [1-sentence description]. Run `/vibeos:build` and I'll start building. I'll check in after each [work order/phase] based on your autonomy preference ([current level])."

### Step 5: Create File Inventory Document
Create `docs/FILE-INVENTORY.md` listing all files the plugin creates:

Organized by:
- **Discovery phase:** project-definition.json, docs/product/*.md
- **Planning phase:** DEVELOPMENT-PLAN.md, WO-INDEX.md, manifests, CLAUDE.md
- **Build phase:** source code, test files, audit reports, baselines
- **Plugin state:** .vibeos/ directory contents
- **Midstream-specific:** findings-registry.json, ACCEPTED-RISKS.md, REMEDIATION-ROADMAP.md

### Step 6: Add File Inventory to Help Skill
Add "files" or "project-files" topic to `skills/help/SKILL.md`:
- When user runs `/vibeos:help files`: show organized list of what the plugin creates and why each file matters

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Test status: Full flow test from install to first build
- Risk: SessionStart hook message could become noisy if it fires every session; keep it brief

## Evidence

- [x] SessionStart suggests first command
- [x] README has Quick Start for greenfield and midstream
- [x] Discover → Plan handoff previews what plan does
- [x] Plan → Build handoff previews first WO
- [x] File inventory document complete
- [x] Help skill supports "files" topic
