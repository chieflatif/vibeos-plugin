# WO-040: End-to-End Integration Testing

## Status

`Complete`

## Phase

Phase 6: Midstream Embedding & Production Readiness

## Objective

Validate the entire VibeOS plugin system end-to-end with both greenfield and midstream scenarios, measuring defect escape rate, convergence, token efficiency, and communication quality.

## Scope

### In Scope
- [x] Greenfield scenario: idea -> discover -> plan -> build 3 WOs -> phase audit
- [x] Midstream scenario: existing project -> baseline -> remediation WO -> build
- [x] Validate defect escape rate: do auditors catch real issues?
- [x] Validate convergence: do fix cycles converge within limits?
- [x] Validate token efficiency: is audit overhead within 30% budget?
- [x] Validate communication quality: is all user-facing output plain English?
- [x] Test full autonomy levels: wo, phase, major
- [x] Test human check-in protocol at each level
- [x] Test plugin upgrade flow
- [x] Generate comprehensive test report

### Out of Scope
- Performance benchmarking (response times)
- Multi-user testing
- Production deployment testing

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-035 | Midstream embedding | Complete |
| WO-036 | Known baselines | Complete |
| WO-037 | Test quality enforcement | Complete |
| WO-038 | Test diff auditing | Complete |
| WO-039 | Plugin upgrade | Complete |

## Impact Analysis

- **Files created:** Test scenarios, test reports
- **Systems affected:** Entire plugin system (validation, not modification)

## Acceptance Criteria

- [x] AC-1: Greenfield scenario completes end-to-end (discover -> plan -> build -> audit)
- [x] AC-2: Midstream scenario completes end-to-end (detect -> baseline -> remediate -> build)
- [x] AC-3: Defect escape rate measured: planted bugs caught / total planted bugs
- [x] AC-4: Convergence verified: fix cycles complete within configured limits
- [x] AC-5: Token efficiency measured: audit overhead < 30%
- [x] AC-6: Communication quality verified: no jargon in user-facing output
- [x] AC-7: All autonomy levels tested and working
- [x] AC-8: Plugin upgrade tested with config preservation

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

- [x] Greenfield scenario completed end-to-end
- [x] Midstream scenario completed end-to-end
- [x] Defect escape rate measured and documented
- [x] Convergence verified
- [x] Token efficiency within budget
- [x] Communication quality verified
- [x] Test report generated
