---
status: In Progress
model_policy: implementation
---
# WO-132 — reusable release amendment

## Objective
Deliver the approved reusable VibeOS changes through the existing generic profile
installer. This amendment covers only the release slice defined in
[the acceptance contract](REUSABLE-HARNESS-RELEASE-AMENDMENT-2026-09-16.md).

## Anchor Alignment
The product promise is governed engineering that preserves each project's own
mission, tests and rules. Reuse exact tested controls and preserve existing
Claude/Cursor surfaces while qualifying the requested macOS/Codex route.

## Research & Freshness
Last verified on 2026-09-16: generic and specialized source comparison, preserved
contribution hashes, live GitHub refs and current pytest/Python primary docs.
Prompt engineering profile: existing project-profile instruction generation;
changes receive literal rendered-surface tests and independent review.

## Approved Deviations
No scope shortcuts. The full vNext programme remains separately tracked.
Native Windows/Linux qualification is outside this macOS release proof.

## Acceptance Criteria
Fresh pinned source installation, project customization, drift refusal and
interrupted recovery pass. Required evidence cannot be empty, stale, skipped,
failed or duplicated. Native execution and PRE_REVIEW publication are verified
separately from owner acceptance. Exact release is reviewed and read back on GitHub.

## Test Strategy
Independent spec-first evaluation tests cover required results, process exits,
source/policy drift, lock contention, symlinks and actual interruption.
Installer and gate agents write negatives before changes. Root runs full suite,
real macOS sandbox proof, two project install smoke cases and fresh-clone replay.
Baseline full suite: 256 passed and 2 failed due to unmarked hook test fixtures;
explicit per-test opt-in corrected the fixtures without weakening assertions.

## Tasks
Follow the bounded implementation and ownership scopes in the acceptance contract.
Root alone integrates, reviews release status, commits and publishes.

### Planning Self-Audit
Audit Status: complete
Primary owner checked source custody, generic reuse, requirement/test mapping,
file ownership and preserved existing source. No new dependency selected.
Known limits: runtime-native sandbox must be exercised outside nested sandbox;
no host-security or unattended-operation claim follows from fixture tests.

### Pre-Implementation Deep Audit
Audit Status: complete
Primary owner inspected the six source modules, fixed-layout assumptions, current
installer and runner. Existing baseline tests ran before edits; new tests derive
from a separately written contract. Real entrypoints are profile analyze/verify/
apply/recover and controlled-evaluation prepare/evaluate/publish. Independent
release review remains pending. Original source and recovery evidence are intact.

### Pre-Commit Audit
Audit Status: complete
Independent implementation review and exact failure-probe replay passed after
corrections. Primary integrated suite: 311 passed, one recursive-gate skip and
51 subtests. Both fresh-installed native project proofs passed. Distribution
readback is a separate release receipt; no application acceptance is inferred.

## Evidence
Evidence and release readback will be recorded in docs/release/2.3.0.md.
