# WO-035: Midstream Embedding

## Status

`Draft`

## Phase

Phase 6: Midstream Embedding & Production Readiness

## Objective

Implement midstream embedding: detect existing code in a target project, run baseline audits, explain findings in plain English, and create remediation WOs with established known baselines.

## Scope

### In Scope
- [ ] Detect existing code in target project (not a greenfield project)
- [ ] Run all 21 gates on existing codebase to establish baseline
- [ ] Run all 5 audit agents on existing codebase
- [ ] Explain all findings in plain English (communication contract)
- [ ] Categorize findings: pre-existing (inherited) vs. new (if any)
- [ ] Create remediation WOs for critical and high findings
- [ ] Establish known baselines: snapshot of current finding counts
- [ ] Store baselines in `.vibeos/baselines/midstream-baseline.json`
- [ ] Integrate into /vibeos:plan (detect existing code, offer midstream flow)

### Out of Scope
- Baseline ratcheting logic (WO-036)
- Plugin upgrade mechanism (WO-039)
- Fixing the findings (remediation WOs handle that)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| Phase 5 complete | Must complete first | Draft |

## Impact Analysis

- **Files created:** midstream detection logic, baseline files
- **Files modified:** skills/plan.md (add midstream detection)
- **Systems affected:** Plan skill, audit pipeline, WO creation

## Acceptance Criteria

- [ ] AC-1: Existing code detected (non-empty src/, lib/, or language-specific directories)
- [ ] AC-2: All gates run and results captured as baseline
- [ ] AC-3: All audit agents run and findings captured as baseline
- [ ] AC-4: Findings explained in plain English with context
- [ ] AC-5: Remediation WOs created for critical/high findings
- [ ] AC-6: Baseline stored in .vibeos/baselines/midstream-baseline.json
- [ ] AC-7: User informed: "These are pre-existing issues. They won't block your new work, but they're tracked for improvement."

## Test Strategy

- **Integration:** Run midstream flow on project with existing code
- **Baseline:** Verify baseline file captures correct finding counts
- **WO creation:** Verify remediation WOs follow template and reference specific findings
- **Greenfield:** Verify midstream flow skipped for empty projects

## Implementation Plan

### Step 1: Implement Code Detection
- Check for source directories (src/, lib/, app/, etc.)
- Check for language indicators (package.json, requirements.txt, go.mod, Cargo.toml)
- If existing code found: trigger midstream flow
- If empty project: skip midstream, proceed with greenfield

### Step 2: Run Baseline Audits
- Execute gate-runner.sh with all gates
- Execute /vibeos:audit for full audit cycle
- Capture all results

### Step 3: Establish Baselines
- Count findings by severity and category
- Store in midstream-baseline.json
- Mark all current findings as "pre-existing"

### Step 4: Create Remediation WOs
- For critical findings: create individual remediation WOs
- For high findings: group related findings into remediation WOs
- For medium/low: document in baseline, no WO required
- Add remediation WOs to DEVELOPMENT-PLAN.md

### Step 5: Explain to User
- Plain English summary of codebase health
- What's good, what needs attention, what's tracked
- Remediation WOs created and their priority

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — run on project with existing code
- Risk: Large existing codebases may produce overwhelming finding counts; must prioritize effectively

## Evidence

- [ ] Existing code detected correctly
- [ ] Baseline audits complete
- [ ] Baseline file stored
- [ ] Remediation WOs created for critical/high findings
- [ ] User explanation is clear and actionable
- [ ] Greenfield projects skip midstream correctly
