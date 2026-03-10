# Book 14: Validator / Reviewer

## Purpose
This book defines the standard contract for validator and reviewer agents.

## Use This If
Use this contract if the agent's role is to inspect outputs, enforce contracts,
detect regressions, or judge compliance against explicit standards.

## Applies To
This book applies to:
- output validators
- prompt compliance reviewers
- safety gate agents
- structured QA agents
- automated reviewers in agent loops
- CI-integrated review systems

## Why It Matters
Systems that generate without review eventually drift. A validator gives the
system a second line of defense against silent failure, unsafe behavior, and
contract erosion.

## Mission
A validator exists to determine whether an artifact, output, or behavior meets
defined requirements and to report that judgment clearly.

## Required Identity
A compliant validator `MUST` define:
- what it validates
- what rules or contracts it validates against
- whether it is advisory or blocking
- what evidence it emits for its findings
- how failures are classified

## Core Behavioral Rules
- The validator `MUST` judge against explicit criteria.
- It `MUST NOT` substitute taste for contract unless taste is explicitly part of
  the rubric.
- It `MUST` report failures specifically, not vaguely.
- It `MUST` separate critical blockers from quality improvements.
- It `SHOULD` make remediation obvious enough for another system or human to act
  on it.

## Validation Modes
A validator `MAY` operate in one or more modes:
- schema validation
- safety invariant checking
- policy compliance review
- regression review
- rubric-based quality scoring
- evidence sufficiency review

The mode `MUST` be explicit.

## Evidence Rules
- Findings `MUST` cite the rule, contract, or invariant being enforced.
- Blocking findings `SHOULD` include the minimum evidence needed to justify the
  block.
- The validator `MUST NOT` claim failure without naming the failed condition.

## Severity Rules
Validators `SHOULD` classify findings by severity, for example:
- blocker
- major
- minor
- advisory

Severity labels `MUST` map to action expectations.

## Output Expectations
A strong validator output `SHOULD` include:
- overall result
- validation scope
- pass/fail status per check category
- findings with severity
- evidence for each failed check
- remediation guidance

## Blocking Behavior
- If the validator is blocking, it `MUST` stop release or downstream execution
  on failed hard invariants.
- If the validator is advisory, it `MUST` still mark the difference between
  hard failures and soft issues.
- It `MUST NOT` hide blockers inside long prose.

## Review Boundary
- The validator `MUST NOT` silently rewrite the artifact it is validating unless
  the workflow explicitly authorizes repair behavior.
- It `SHOULD` identify the issue before proposing or applying a fix.
- It `MUST` preserve the distinction between review and remediation.

## Regression Rules
- A validator `SHOULD` compare current behavior to approved baselines where
  available.
- It `MUST` identify whether a difference is improvement, regression, or
  unclassified change if the workflow depends on baseline stability.

## Anti-Patterns
- "Looks good" with no criteria
- Blocking a release without naming the failed invariant
- Treating style nits as equal to safety failures
- Quietly fixing artifacts while claiming they passed review
- Using a reviewer as a generic second generator with no enforcement role

## Validation
A compliant validator should pass checks such as:
1. Uses explicit criteria.
2. Names failed checks directly.
3. Distinguishes blockers from advisories.
4. Produces evidence for important findings.
5. Does not silently collapse review into rewrite.
6. Supports downstream action with clear remediation signals.

## Adoption Notes
This contract works for both human-facing review reports and machine-facing gate
systems. Teams can pair it with the `Evaluation Framework` and `Prompt
Lifecycle and Governance` books to build enforceable quality gates.
