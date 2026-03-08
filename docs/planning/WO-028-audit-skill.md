# WO-028: /vibeos:audit Skill (Full Audit Cycle)

## Status

`Draft`

## Phase

Phase 4: Fresh-Context Audit Agents

## Objective

Create a `/vibeos:audit` skill that dispatches all 5 audit agents, applies consensus logic, and produces a composite report in communication contract format.

## Scope

### In Scope
- [ ] Create `skills/audit.md` as the audit orchestrator
- [ ] Dispatch all 5 audit agents: security, architecture, correctness, test, evidence
- [ ] Collect structured findings from each agent
- [ ] Apply consensus logic: 2+ agents flag same issue = true positive, 1 agent = warning
- [ ] Generate composite report combining all findings
- [ ] Report in communication contract format (plain English, severity, action items)
- [ ] Summary section: total findings by severity, consensus findings, warnings

### Out of Scope
- Individual audit agent implementation (WO-023-027)
- Build loop integration (WO-029)
- Phase boundary audit (WO-033)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-023 | Security auditor | Draft |
| WO-024 | Architecture auditor | Draft |
| WO-025 | Correctness auditor | Draft |
| WO-026 | Test auditor | Draft |
| WO-027 | Evidence auditor | Draft |

## Impact Analysis

- **Files created:** skills/audit.md
- **Systems affected:** Audit pipeline, build loop (future integration)

## Acceptance Criteria

- [ ] AC-1: All 5 audit agents dispatched successfully
- [ ] AC-2: Findings collected and merged into unified format
- [ ] AC-3: Consensus logic applied: 2+ agents = true positive, 1 = warning
- [ ] AC-4: Composite report generated with all findings grouped by severity
- [ ] AC-5: Report uses communication contract language (plain English, no jargon)
- [ ] AC-6: Summary includes: finding counts, consensus items, action items
- [ ] AC-7: Report identifies which auditor(s) flagged each finding

## Test Strategy

- **Integration:** Dispatch full audit cycle against sample code
- **Consensus:** Verify consensus logic with overlapping findings from multiple agents
- **Report:** Verify composite report is readable and actionable

## Implementation Plan

### Step 1: Create Skill File
- Define skill metadata
- Dispatch sequence: all 5 agents (can run in parallel where isolation allows)

### Step 2: Implement Finding Merging
- Normalize finding format across all agents
- Group by file/location
- Identify overlapping findings (same file, similar description)

### Step 3: Implement Consensus Logic
- For each unique finding location: count how many agents flagged it
- 2+ agents: mark as true positive (high confidence)
- 1 agent: mark as warning (review recommended)
- 0 agents: clean (no issues)

### Step 4: Generate Composite Report
- Header: audit scope, date, agents dispatched
- Section per severity level: critical, high, medium, low
- Each finding: description, auditors that flagged it, consensus status, recommendation
- Summary: counts, top risks, action items

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — full audit cycle with consensus
- Risk: 5 agents dispatched = significant token cost; must balance thoroughness with efficiency

## Evidence

- [ ] Skill file created
- [ ] All 5 agents dispatched successfully
- [ ] Consensus logic working (overlapping findings merged)
- [ ] Composite report generated
- [ ] Report uses communication contract language
