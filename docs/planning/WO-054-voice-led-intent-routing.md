# WO-054: Voice-Led Intent Routing

## Status

`Complete`

## Phase

Phase 9: Conversational Experience

## Objective

Eliminate the need for slash commands by making VibeOS fully voice-led. Users describe what they want in natural language ("I want to build a task management app", "how's my project going?", "check the code quality") and the system automatically routes to the correct skill with lifecycle-aware context. Slash commands remain as power-user shortcuts but are never required.

## Problem Statement

Today, all 9 skills require explicit `/vibeos:*` invocation. This creates three problems:

1. **Discoverability barrier** — Users must know which command exists before they can use it. The system is invisible until someone reads the help or README.
2. **Voice/conversational incompatibility** — Voice-to-text produces natural language, not slash commands. A voice-led user cannot say "forward slash vibeos colon discover."
3. **Cognitive load** — Choosing between `/vibeos:gate`, `/vibeos:audit`, and `/vibeos:checkpoint` requires understanding the plugin's internal architecture. The Communication Contract says users shouldn't need to understand mechanisms.

## Design Constraints

1. **No forced routing** — `UserPromptSubmit` hooks can inject `additionalContext` but cannot force skill invocation. Claude must decide. The routing system provides strong hints, not directives.
2. **Lifecycle awareness** — The same phrase ("let's get started") means different things at different project stages. Routing must read `.vibeos/` state.
3. **Governed vs. direct help** — Some requests should trigger governed skills (build, audit). Others should be handled directly by Claude (explain this error, help me understand this code). The router must distinguish.
4. **No-ask principle** — The Communication Contract says the agent never asks "what do you want to build?" once a plan exists. Routing must respect this.
5. **Backward compatible** — Explicit `/vibeos:*` commands continue to work exactly as before.
6. **Performance** — The UserPromptSubmit hook fires on every user message. It must be fast (<200ms).

## Scope

### In Scope
- [ ] `UserPromptSubmit` hook script that reads user prompt + project lifecycle state and injects routing context
- [ ] Lifecycle state detection logic (what stage is this project at?)
- [ ] Intent classification logic (what skill does this message map to?)
- [ ] Disambiguation protocol (what to do when intent is ambiguous)
- [ ] CLAUDE.md routing instructions that tell the model to follow routing hints
- [ ] Skill description enrichment with natural language trigger phrases
- [ ] Updated onboarding messages to use conversational language instead of slash commands
- [ ] Updated SessionStart hook with lifecycle-aware welcome message
- [ ] Conflict resolution rules (governed skill vs. direct help)

### Out of Scope
- Changing how skills work internally (skills still receive `$ARGUMENTS` the same way)
- Adding new skills
- Removing slash command support
- Voice input handling (that's the user's OS/app layer)
- AI-based intent classification (this is pattern matching in bash, not ML)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| Phase 8 | All Phase 8 WOs | Complete |
| UserPromptSubmit hook event | Claude Code feature | Available (verified) |
| .vibeos/ state files | Config, plan, baselines | Defined in WO-030+ |

## Architecture

### Two-Layer Routing System

```
User message
    │
    ▼
┌─────────────────────────┐
│  Layer 1: Hook Script    │  UserPromptSubmit event
│  (intent-router.sh)      │  Fires on every message
│                           │
│  1. Read project state    │  .vibeos/config.json, project-definition.json,
│  2. Classify intent       │  DEVELOPMENT-PLAN.md, WO-INDEX.md
│  3. Inject routing hint   │  additionalContext in JSON output
└───────────┬───────────────┘
            │ routing hint injected into context
            ▼
┌─────────────────────────┐
│  Layer 2: CLAUDE.md      │  Model reads routing instructions
│  Routing Instructions    │  + hook's additionalContext
│                           │
│  1. Follow routing hint   │  "The intent router suggests /vibeos:discover"
│  2. Apply conflict rules  │  "If the user is asking about code, help directly"
│  3. Invoke skill or help  │  Model decides final action
└───────────────────────────┘
```

### Lifecycle States

The hook script determines project stage by checking file existence:

| State | Detection | Default Skill |
|---|---|---|
| `virgin` | No `.vibeos/config.json` | discover |
| `discovered` | `project-definition.json` exists, no `DEVELOPMENT-PLAN.md` | plan |
| `planned` | `DEVELOPMENT-PLAN.md` exists, no WOs started | build |
| `building` | Active WOs in `WO-INDEX.md` | build (continue) |
| `checkpoint` | `.vibeos/checkpoints/` has resume state | build (resume) |
| `phase-boundary` | All WOs in current phase complete | checkpoint |
| `complete` | All phases complete | status |

### Intent Categories

| Category | Trigger Patterns | Maps To | Confidence |
|---|---|---|---|
| `create` | "build", "make", "create", "I want to", "new project", "idea" | discover (virgin) or build (planned+) | High |
| `plan` | "plan", "break down", "organize", "phases", "roadmap" | plan | High |
| `progress` | "status", "how's it going", "progress", "where are we" | status | High |
| `quality` | "check", "quality", "test", "passing", "gates" | gate | Medium |
| `review` | "review", "audit", "security", "look over" | audit | Medium |
| `explain` | "what is", "explain", "help", "how does", "what does" | help | High |
| `continue` | "continue", "next", "keep going", "resume", "go" | build | High |
| `manage` | "work order", "wo", "create wo", "wo status" | wo | High |
| `milestone` | "phase done", "milestone", "checkpoint", "phase complete" | checkpoint | Medium |
| `direct` | Code-specific questions, error messages, file references | None (Claude helps directly) | Low |

### Disambiguation Protocol

When confidence is Medium or Low, or when multiple categories match:

1. **State tiebreaker** — Use lifecycle state to pick the most likely skill (e.g., "check this" at `building` stage → gate, not audit)
2. **Governed vs. direct** — If the message references specific files/lines/errors, it's likely a direct help request, not a skill invocation
3. **Explicit confirmation** — If still ambiguous after state tiebreaker, the routing hint tells Claude to briefly confirm: "It sounds like you want to [X]. Should I [action], or were you asking about something else?"

### Conflict Resolution: Governed vs. Direct

```
IF message contains file paths, line numbers, error messages, or code snippets:
  → Route to direct help (no skill invocation)
  → Exception: if user says "build this" or "fix this with the build system"

IF message is about a concept or term:
  → Route to /vibeos:help

IF message describes a product idea AND state is virgin/discovered:
  → Route to /vibeos:discover

IF message says "continue" or "next" AND state is building:
  → Route to /vibeos:build (resume current WO)

IF message is vague AND state is virgin:
  → Route to /vibeos:discover (default for new projects)

IF message is vague AND state is building:
  → Route to /vibeos:status (show dashboard, let user decide)
```

## Acceptance Criteria

- [ ] AC-1: UserPromptSubmit hook script exists, is executable, runs in <200ms
- [ ] AC-2: Hook correctly detects all 7 lifecycle states from file existence checks
- [ ] AC-3: Hook injects valid JSON with `additionalContext` containing routing hint
- [ ] AC-4: CLAUDE.md contains routing instructions that reference the hook's hints
- [ ] AC-5: All 9 skill descriptions enriched with natural language trigger phrases
- [ ] AC-6: User saying "I want to build a task management app" on a virgin project triggers discover without typing any slash command
- [ ] AC-7: User saying "how's it going?" triggers status
- [ ] AC-8: User asking "what does ratcheting mean?" triggers help, not a skill
- [ ] AC-9: User referencing a specific file/error gets direct help, not skill routing
- [ ] AC-10: Ambiguous intents produce a brief confirmation, not a wrong skill invocation
- [ ] AC-11: Explicit `/vibeos:*` commands continue to work unchanged
- [ ] AC-12: Onboarding welcome message uses conversational language, not slash commands
- [ ] AC-13: SessionStart hook outputs lifecycle-aware welcome (not just "try /vibeos:discover")
- [ ] AC-14: Communication Contract updated with routing-related patterns

## Test Strategy

- **Hook performance:** Time the intent-router.sh script — must complete in <200ms on all lifecycle states
- **Intent classification:** Create a test matrix of 30+ natural language phrases, verify each maps to the correct skill or "direct help"
- **Lifecycle detection:** Create mock .vibeos/ directories for each of the 7 states, verify correct detection
- **End-to-end:** Load plugin, say "I have an idea for a project" — verify discover starts without slash command
- **Backward compat:** Load plugin, say "/vibeos:discover" — verify it still works
- **Disambiguation:** Say "check this" at different lifecycle states — verify different routing
- **Direct help:** Say "what's wrong with line 42 of app.py" — verify no skill invocation
- **Regression:** All existing smoke test scenarios still pass

## Impact Analysis

- **Files created:**
  - `hooks/scripts/intent-router.sh` — UserPromptSubmit hook script
  - `docs/planning/WO-054-voice-led-intent-routing.md` — this WO
- **Files modified:**
  - `hooks/hooks.json` — add UserPromptSubmit event with intent-router.sh
  - `CLAUDE.md` — add Intent Routing section with routing instructions
  - `hooks/scripts/prereq-check.sh` — lifecycle-aware welcome message
  - `skills/*/SKILL.md` (all 9) — enrich description fields with trigger phrases
  - `docs/USER-COMMUNICATION-CONTRACT.md` — add routing communication patterns
  - `skills/discover/SKILL.md` — update onboarding to conversational language
  - `skills/build/SKILL.md` — update onboarding to conversational language
  - `skills/help/SKILL.md` — update onboarding to conversational language
  - `README.md` — update Quick Start to show conversational examples alongside slash commands
- **Systems affected:** User interaction model (fundamental UX shift from command-driven to conversation-driven)

## Implementation Plan

### Step 1: Lifecycle State Detection
Write the state detection logic as a bash function that checks file existence and returns one of the 7 lifecycle states. This is the foundation everything else depends on.

- Read `.vibeos/config.json` for `onboarding_complete`
- Check `project-definition.json` existence
- Check `docs/planning/DEVELOPMENT-PLAN.md` existence
- Parse `docs/planning/WO-INDEX.md` for active/complete WOs
- Check `.vibeos/checkpoints/` for resume state
- Return: `virgin | discovered | planned | building | checkpoint | phase-boundary | complete`

### Step 2: Intent Classification
Write pattern matching logic that classifies the user's prompt into one of the 10 intent categories. Uses grep/regex, not AI.

- Match against trigger patterns (case-insensitive)
- Score each category by number of matching patterns
- Apply lifecycle state as tiebreaker
- Detect "direct help" signals (file paths, error messages, code references)
- Return: `{ intent, skill, confidence, reasoning }`

### Step 3: Hook Script Assembly
Combine Steps 1 and 2 into `hooks/scripts/intent-router.sh`:

- Read user prompt from hook input (stdin JSON, `prompt` field)
- Run lifecycle detection
- Run intent classification
- Format routing hint as `additionalContext`
- Output valid JSON
- Target: <200ms total execution time

### Step 4: Hook Wiring
Add `UserPromptSubmit` event to `hooks/hooks.json`:

```json
"UserPromptSubmit": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/intent-router.sh"
      }
    ]
  }
]
```

### Step 5: CLAUDE.md Routing Instructions
Add a section to CLAUDE.md that tells the model:

- How to interpret routing hints from the intent-router hook
- When to follow the hint vs. when to override (direct help scenarios)
- How to handle disambiguation (brief confirmation, not interrogation)
- That slash commands are never required — conversational input is the primary interface
- The conflict resolution rules (governed skill vs. direct help)

### Step 6: Skill Description Enrichment
Update each SKILL.md's `description` field with richer natural language triggers:

- **discover:** Add "Use when the user has an idea, wants to start something new, describes a product, or says 'I want to build...'"
- **build:** Add "Use when the user says 'continue', 'keep going', 'build the next thing', or 'resume'"
- **status:** Add "Use when the user asks about progress, what's happening, or where things stand"
- etc.

### Step 7: Onboarding & Communication Updates
- Update onboarding messages in discover, build, help skills to use conversational language
- Replace "Try `/vibeos:discover`" with "Just tell me what you want to build, or ask me anything about how the system works"
- Update SessionStart prereq-check.sh to be lifecycle-aware
- Add routing-related patterns to Communication Contract

### Step 8: Test Matrix Validation
Create and run the intent classification test matrix:
- 30+ phrases covering all intent categories
- Each lifecycle state
- Ambiguous cases
- Direct help cases
- Verify routing accuracy > 90%

## Risk Analysis

| Risk | Severity | Mitigation |
|---|---|---|
| Model ignores routing hints | High | Strong CLAUDE.md instructions + rich skill descriptions as backup |
| False positives (wrong skill triggered) | Medium | Disambiguation protocol + confirmation for medium/low confidence |
| Hook adds latency to every message | Low | Target <200ms, file existence checks are fast |
| Pattern matching too rigid | Medium | Start conservative, iterate based on real usage |
| Breaks existing slash command flow | Low | Slash commands bypass the router entirely |

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Findings: —
- Key questions: Is the two-layer routing architecture sufficient? Are the intent categories comprehensive? Is the disambiguation protocol clear enough?

### Pre-Implementation Audit
- Status: `pending`
- Findings: —
- Test status: —

### Pre-Commit Audit
- Status: `pending`
- Findings: —
- Test status: —

## Evidence

- [ ] Hook script exists and is executable
- [ ] Hook runs in <200ms
- [ ] Intent test matrix passes at >90% accuracy
- [ ] End-to-end test: natural language → skill invocation
- [ ] Backward compat: slash commands still work
- [ ] All modified files pass quality gates
- [ ] Communication Contract updated
- [ ] CLAUDE.md routing section complete
