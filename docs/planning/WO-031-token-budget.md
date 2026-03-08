# WO-031: Token Budget Tracking

## Status

`Draft`

## Phase

Phase 5: Convergence & Full Autonomous Loop

## Objective

Track token usage per agent, per WO, and per phase, with alerts when audit overhead exceeds 30% of total token spend.

## Scope

### In Scope
- [ ] Track token usage per agent dispatch (input tokens, output tokens)
- [ ] Aggregate by WO: total tokens for investigator, tester, implementer, auditors
- [ ] Aggregate by phase: total tokens across all WOs in phase
- [ ] Calculate audit overhead: (audit tokens / total tokens) as percentage
- [ ] Alert when audit overhead exceeds 30%
- [ ] Store token data in `.vibeos/token-usage.json`
- [ ] Report token usage in build-log.md entries

### Out of Scope
- Token cost calculation (pricing varies)
- Token optimization (separate concern)
- Model selection optimization based on token usage

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-030 | Must complete first | Draft |

## Impact Analysis

- **Files created:** .vibeos/token-usage.json schema
- **Files modified:** skills/build.md (add token tracking)
- **Systems affected:** Build loop, agent dispatch, reporting

## Acceptance Criteria

- [ ] AC-1: Token usage recorded for every agent dispatch
- [ ] AC-2: Per-WO aggregation available
- [ ] AC-3: Per-phase aggregation available
- [ ] AC-4: Audit overhead percentage calculated correctly
- [ ] AC-5: Alert generated when audit overhead exceeds 30%
- [ ] AC-6: Token data persisted to .vibeos/token-usage.json
- [ ] AC-7: Build log includes token usage per dispatch

## Test Strategy

- **Unit:** Test aggregation logic with sample token data
- **Integration:** Run build, verify token data recorded
- **Alert:** Simulate high audit overhead, verify alert generated

## Implementation Plan

### Step 1: Implement Token Capture
- After each agent dispatch: capture token usage from response
- Record: agent name, WO, timestamp, input_tokens, output_tokens
- Append to token-usage.json

### Step 2: Implement Aggregation
- Per-WO: sum all agent dispatches for a WO
- Per-phase: sum all WOs in a phase
- Audit overhead: sum(audit agent tokens) / sum(all tokens)

### Step 3: Implement Alerting
- After each dispatch: recalculate audit overhead
- If > 30%: log warning to build-log.md
- Include breakdown: which audit agents used most tokens

### Step 4: Implement Reporting
- Add token summary to build-log.md entries
- Include in escalation reports

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Unit tests for aggregation, integration test for capture
- Risk: Token usage may not be easily accessible from agent dispatch API; may need platform-specific approach

## Evidence

- [ ] Token usage recorded per dispatch
- [ ] Aggregation by WO and phase works
- [ ] Audit overhead alert triggers at 30%
- [ ] Token data persisted to JSON
