# WO-040: End-to-End Integration Testing

## Status

`Draft`

## Phase

Phase 6: Midstream Embedding & Production Readiness

## Objective

Validate the entire VibeOS plugin system end-to-end with both greenfield and midstream scenarios, measuring defect escape rate, convergence, token efficiency, and communication quality.

## Scope

### In Scope
- [ ] Greenfield scenario: idea -> discover -> plan -> build 3 WOs -> phase audit
- [ ] Midstream scenario: existing project -> baseline -> remediation WO -> build
- [ ] Validate defect escape rate: do auditors catch real issues?
- [ ] Validate convergence: do fix cycles converge within limits?
- [ ] Validate token efficiency: is audit overhead within 30% budget?
- [ ] Validate communication quality: is all user-facing output plain English?
- [ ] Test full autonomy levels: wo, phase, major
- [ ] Test human check-in protocol at each level
- [ ] Test plugin upgrade flow
- [ ] Generate comprehensive test report

### Out of Scope
- Performance benchmarking (response times)
- Multi-user testing
- Production deployment testing

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-035 | Midstream embedding | Draft |
| WO-036 | Known baselines | Draft |
| WO-037 | Test quality enforcement | Draft |
| WO-038 | Test diff auditing | Draft |
| WO-039 | Plugin upgrade | Draft |

## Impact Analysis

- **Files created:** Test scenarios, test reports
- **Systems affected:** Entire plugin system (validation, not modification)

## Acceptance Criteria

- [ ] AC-1: Greenfield scenario completes end-to-end (discover -> plan -> build -> audit)
- [ ] AC-2: Midstream scenario completes end-to-end (detect -> baseline -> remediate -> build)
- [ ] AC-3: Defect escape rate measured: planted bugs caught / total planted bugs
- [ ] AC-4: Convergence verified: fix cycles complete within configured limits
- [ ] AC-5: Token efficiency measured: audit overhead < 30%
- [ ] AC-6: Communication quality verified: no jargon in user-facing output
- [ ] AC-7: All autonomy levels tested and working
- [ ] AC-8: Plugin upgrade tested with config preservation

## Test Strategy

- **Greenfield E2E:** Create test project idea, run full flow, verify 3 WOs built
- **Midstream E2E:** Use existing test project, run midstream flow, verify baseline and remediation
- **Metrics:** Measure and report defect escape rate, convergence, token usage
- **Communication:** Review all user-facing output for contract compliance

## Implementation Plan

### Step 1: Create Greenfield Test Scenario
- Define a simple but realistic project idea (e.g., "build a task tracker API")
- Run /vibeos:discover with test inputs
- Run /vibeos:plan
- Run /vibeos:build for 3 WOs
- Run /vibeos:checkpoint
- Verify all steps complete and artifacts produced

### Step 2: Create Midstream Test Scenario
- Use a test project with existing code and known issues
- Run midstream detection and baseline
- Verify remediation WOs created
- Build one remediation WO
- Verify baseline ratchets down

### Step 3: Measure Metrics
- Defect escape rate: plant N bugs, count how many auditors catch
- Convergence: track fix cycle counts across all WOs
- Token efficiency: read token-usage.json, calculate audit percentage
- Communication: scan all output for jargon patterns

### Step 4: Generate Test Report
- Summary: pass/fail per scenario
- Metrics: defect escape rate, convergence stats, token efficiency
- Communication audit: jargon instances found
- Recommendations: areas for improvement

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: This WO IS the test — success criteria are the acceptance criteria
- Risk: E2E testing is expensive in tokens; must be structured to maximize coverage with minimum cost

## Evidence

- [ ] Greenfield scenario completed end-to-end
- [ ] Midstream scenario completed end-to-end
- [ ] Defect escape rate measured and documented
- [ ] Convergence verified
- [ ] Token efficiency within budget
- [ ] Communication quality verified
- [ ] Test report generated
