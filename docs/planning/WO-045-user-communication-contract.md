# WO-045: User Communication Contract

## Status

`Draft`

## Phase

Phase 7: Informed Onboarding & User Comprehension

## Objective

Create the `USER-COMMUNICATION-CONTRACT.md` referenced in CLAUDE.md but never built. This document defines the universal rules for all user-facing communication: how to introduce concepts, format progress updates, present decisions with consequences, explain errors, and maintain a consistent voice. Every agent and skill embeds this contract.

## Scope

### In Scope
- [ ] Create `docs/USER-COMMUNICATION-CONTRACT.md` with universal communication rules
- [ ] Define concept introduction protocol: first use of any term includes plain English definition
- [ ] Define progress reporting format: step indicators, agent identification, ETA-free status
- [ ] Define decision presentation format: options with consequences, not just labels
- [ ] Define error reporting format: what happened, why, what was tried, options
- [ ] Define escalation format: when the system needs human input
- [ ] Define finding presentation format: risk in business terms, not technical jargon
- [ ] Define glossary of core terms (WO, phase, gate, audit, convergence, baseline, ratchet, TDD, layer)
- [ ] Embed contract reference in every agent prompt (agents/*.md)
- [ ] Embed contract reference in every skill prompt (skills/*/SKILL.md)
- [ ] Add communication contract to agent frontmatter as a constraint

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

- [ ] AC-1: USER-COMMUNICATION-CONTRACT.md created with all sections
- [ ] AC-2: Concept introduction protocol defined with examples
- [ ] AC-3: Progress reporting format defined with templates
- [ ] AC-4: Decision presentation format defined with consequence requirements
- [ ] AC-5: Error reporting format defined
- [ ] AC-6: Glossary of 15+ core terms with plain English definitions
- [ ] AC-7: All 12 agent files reference the communication contract
- [ ] AC-8: All 8 skill files reference the communication contract
- [ ] AC-9: Contract is testable — a reviewer can check if output complies

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

### Step 2: Define Output Templates
Mandatory templates for common outputs:
- **Progress update:** `"[Step N/M] [agent-name] — [what it's doing in plain English]"`
- **Gate result:** `"Quality check: [N] passed, [M] need attention. [Top issue in plain English]"`
- **Audit finding:** `"[severity]: [what's wrong] in [file]. [Why it matters]. [What to do about it]."`
- **Decision point:** `"[Question]. Option A: [description] — [consequence]. Option B: [description] — [consequence]. I recommend [X] because [reason]."`
- **Error/escalation:** `"Something went wrong: [what happened in plain English]. I tried: [what was attempted]. Your options: [list with consequences]."`

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
For each agent file, add to the prompt:
```
## Communication Contract
Follow the USER-COMMUNICATION-CONTRACT.md when producing any user-facing output.
All findings must be explained in plain English with business impact.
Technical terms must be accompanied by their glossary definition on first use.
```

For each skill file, add to Communication Contract section:
```
Follow the full USER-COMMUNICATION-CONTRACT.md. Key rules:
- Lead with outcome, follow with mechanism
- Present decisions with consequences
- Introduce every concept on first use with plain English definition
```

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Review all agent/skill files for contract reference, sample output compliance
- Risk: Contract is an instruction to the AI, not enforced code — compliance is probabilistic. Templates and examples improve compliance rate.

## Evidence

- [ ] Communication contract document created
- [ ] All agents reference contract
- [ ] All skills reference contract
- [ ] Glossary covers all core terms
- [ ] Output templates are clear and testable
