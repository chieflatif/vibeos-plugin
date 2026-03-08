# WO-045: User Communication Contract

## Status

`Complete`

## Phase

Phase 7: Informed Onboarding & User Comprehension

## Objective

Create the `USER-COMMUNICATION-CONTRACT.md` referenced in CLAUDE.md but never built. This document defines the universal rules for all user-facing communication: how to introduce concepts, format progress updates, present decisions with consequences, explain errors, and maintain a consistent voice. Every agent and skill embeds this contract.

## Scope

### In Scope
- [x]Create `docs/USER-COMMUNICATION-CONTRACT.md` with universal communication rules
- [x]Define concept introduction protocol: first use of any term includes plain English definition
- [x]Define progress reporting format: step indicators, agent identification, ETA-free status
- [x]Define decision presentation format: options with consequences, not just labels
- [x]Define error reporting format: what happened, why, what was tried, options
- [x]Define escalation format: when the system needs human input
- [x]Define finding presentation format: risk in business terms, not technical jargon
- [x]Define glossary of core terms (WO, phase, gate, audit, convergence, baseline, ratchet, TDD, layer)
- [x]Embed contract reference in every agent prompt (agents/*.md)
- [x]Embed contract reference in every skill prompt (skills/*/SKILL.md)
- [x]Add communication contract to agent frontmatter as a constraint

### Out of Scope
- Onboarding flow (WO-046)
- Build loop progress reporting implementation (WO-047)
- Decision support implementation (WO-048)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| Phase 6 complete | Must complete first | Complete |

## Impact Analysis

- **Files created:** `docs/USER-COMMUNICATION-CONTRACT.md`
- **Files modified:** All 12 agent files (add contract reference), all 8 skill files (add contract reference)
- **Systems affected:** Every user-facing output in the entire plugin

## Acceptance Criteria

- [x]AC-1: USER-COMMUNICATION-CONTRACT.md created with all sections
- [x]AC-2: Concept introduction protocol defined with examples
- [x]AC-3: Progress reporting format defined with templates
- [x]AC-4: Decision presentation format defined with consequence requirements
- [x]AC-5: Error reporting format defined
- [x]AC-6: Glossary of 15+ core terms with plain English definitions
- [x]AC-7: All 12 agent files reference the communication contract
- [x]AC-8: All 8 skill files reference the communication contract
- [x]AC-9: Contract includes at least one compliant and one non-compliant example for each template, enabling objective compliance checking

## Test Strategy

- **Review:** Read every agent and skill file, verify contract is referenced
- **Compliance:** Sample outputs from build/audit/plan skills, verify against contract rules
- **Glossary:** Verify every term used in user-facing output has a glossary definition

## Implementation Plan

### Step 1: Define Communication Principles
Core rules:
1. **Lead with outcome, follow with mechanism.** "Your code passed 12 quality checks" before "gate-runner.sh executed pre_commit phase."
2. **Introduce every concept on first use.** "I'm creating a work order (WO) — a detailed specification for one unit of work, like building a feature or fixing a bug."
3. **Present decisions with consequences.** Not "skip gates?" but "skip these quality checks — your code will be committed without verifying [specific things]. You can re-run them later."
4. **Explain errors in terms of impact.** Not "exit code 1 from validate-types.sh" but "your type annotations are incomplete — 3 functions are missing return types, which means bugs could slip through undetected."
5. **Never use a technical term without context.** Not "ratchet violation" but "quality regression — the number of issues increased since the last phase, which our one-way improvement policy doesn't allow."

### Step 2: Define Output Template Schemas
Define the **template structure** for common outputs. These are the base schemas — WO-047 (build visibility) and WO-048 (consequence decisions) will populate specific instances within this structure. WO-045 defines the schema and initial templates; WO-047/048 add domain-specific variants that must conform to these schemas.

**Template schemas:**
- **Progress update:** `"[Step N/M] [agent-name] — [what it's doing in plain English]"` — WO-047 adds specific build loop step variants
- **Gate result:** `"Quality check: [N] passed, [M] need attention. [Top issue in plain English]"` — WO-047 adds inline gate reporting format
- **Audit finding:** `"[severity]: [what's wrong] in [file]. [Why it matters]. [What to do about it]."`
- **Decision point:** `"[Context]. Option A: [description] — [consequence]. Option B: [description] — [consequence]. I recommend [X] because [reason]."` — WO-048 adds domain-specific decision rewrites that conform to this schema
- **Error/escalation:** `"Something went wrong: [what happened in plain English]. I tried: [what was attempted]. Your options: [list with consequences]."`
- **System notification:** `"[notification type]: [message in plain English]"` — for non-step messages like aging reminders (WO-044), convergence updates, etc.

### Step 3: Define Glossary
Core terms with definitions:
- **Work Order (WO):** A detailed specification for one unit of work — like a task card with acceptance criteria
- **Phase:** A group of related WOs that together deliver a milestone
- **Quality Gate:** An automated check that runs before code is committed — like a safety inspection
- **Audit Agent:** A specialized reviewer that examines your code for specific types of issues
- **Consensus:** When 2 or more audit agents flag the same issue — this makes it a confirmed finding
- **Baseline:** A snapshot of your codebase's current quality level — the starting point
- **Ratchet:** A rule that quality can only improve, never get worse — like a one-way valve
- **Convergence:** The process of fix cycles getting closer to zero issues
- **TDD (Test-Driven Development):** Writing tests before code — the tests define what "working" means
- **Layer:** One level of the quality enforcement system (there are 7 layers total)
- ... (15+ terms total)

### Step 4: Embed in Agents and Skills
**Agent reference path:** Use `${CLAUDE_PLUGIN_ROOT}/docs/USER-COMMUNICATION-CONTRACT.md` — `${CLAUDE_PLUGIN_ROOT}` is available in hooks (confirmed by Phase 0 spike) and should be available in agent execution contexts since agents run within the plugin environment.

For each agent file, add to the prompt:
```
## Communication Contract
Read and follow ${CLAUDE_PLUGIN_ROOT}/docs/USER-COMMUNICATION-CONTRACT.md when producing any user-facing output.
All findings must be explained in plain English with business impact.
Technical terms must be accompanied by their glossary definition on first use.
```

For each skill file: **replace** the existing inline `## Communication Contract` sections (currently present in all 8 skills with ad-hoc rules) with a standardized reference to the centralized contract plus any skill-specific communication rules that go beyond the contract:
```
## Communication Contract
Follow the full USER-COMMUNICATION-CONTRACT.md (${CLAUDE_PLUGIN_ROOT}/docs/USER-COMMUNICATION-CONTRACT.md). Key rules:
- Lead with outcome, follow with mechanism
- Present decisions with consequences
- Introduce every concept on first use with plain English definition
[Skill-specific rules below if any]
```

**Migration strategy:** Existing inline rules in skills are replaced, not supplemented. Any skill-specific rules not covered by the centralized contract are preserved as skill-specific addenda below the contract reference.

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Test status: Review all agent/skill files for contract reference, sample output compliance
- Risk: Contract is an instruction to the AI, not enforced code — compliance is probabilistic. Templates and examples improve compliance rate.

## Evidence

- [x]Communication contract document created
- [x]All agents reference contract
- [x]All skills reference contract
- [x]Glossary covers all core terms
- [x]Output templates are clear and testable
