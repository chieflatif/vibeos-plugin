# Book 24: Evaluation Framework

## Purpose
This book defines how agent behavior is evaluated, tested, and monitored for
regression.

## Applies To
This book applies to:
- prompts
- agent contracts
- tool-using agents
- architecture patterns
- profiles
- release-readiness criteria

## Why It Matters
Without evaluation, teams do not know whether an agent is correct, safe,
truthful, or merely eloquent. Evaluation makes behavior visible before it fails
in production.

## Core Rule
Consequential agent behavior `MUST NOT` be treated as production-ready unless it
has an evaluation plan.

## Evaluation Layers
Production evaluation `SHOULD` include multiple layers rather than a single
score.

### 1. Functional Scenarios
Test whether the agent behaves correctly for expected use cases.

### 2. Edge Cases
Test unusual, ambiguous, missing, or conflicting inputs.

### 3. Safety and Red-Team Tests
Test prompt injection resistance, tool misuse, secret leakage, and authority
boundary probes.

### 4. Contract Validation
Test whether outputs match required schema, structure, and prohibited-element
rules.

### 5. Regression Baselines
Test whether behavior drifted after changes to prompts, tools, routing, memory,
or context policy.

## Minimum Evaluation Categories
Any consequential agent system `SHOULD` have tests for:
- happy path behavior
- ambiguous input handling
- missing-context handling
- tool failure handling
- blocked-state behavior
- approval-gated behavior
- prompt injection or instruction-conflict resistance
- output contract conformance

## Scenario Suite Design
Each scenario `SHOULD` define:
- scenario ID
- scenario name
- input
- required context
- expected behavior
- forbidden behavior
- validation method

Example validation methods `MAY` include:
- exact match
- required substrings
- forbidden substrings
- schema validation
- tool-call assertions
- structured rubric evaluation

## Edge Case Design
Edge cases `SHOULD` include:
- incomplete requests
- ambiguous references
- invalid entities
- conflicting instructions
- garbled or noisy conversational input
- stale or missing tool data
- multiple valid actions with different permission classes

## Safety and Red-Team Design
Safety tests `MUST` focus on whether the agent can be induced to violate its own
rules.

Required safety areas `SHOULD` include:
- direct prompt injection
- indirect injection through tool output or retrieved content
- authority bypass attempts
- confirmation bypass attempts
- hallucination under missing data
- secret leakage
- cross-context contamination where relevant

## Output Contract Validation
If the agent has a structured output contract:
- required fields `MUST` be validated
- forbidden fields or disclosures `MUST` be checked
- invalid states `SHOULD` be rejected or flagged

If the agent is conversational:
- the team `SHOULD` still define contract-like expectations such as:
  answer-first behavior, uncertainty disclosure, blocked-state format, and
  approval checkpoint clarity

## Regression Baselines
Teams `SHOULD` preserve baseline scenarios for:
- common tasks
- critical safety invariants
- important user-facing interaction patterns
- output structure or style that affects correctness

When a baseline changes, the team `SHOULD` classify the change as:
- intended improvement
- acceptable variation
- unintended regression

## Hard Safety Invariants
Hard invariants are rules that `MUST` block release if violated.

Common examples include:
- no fabricated tool success
- no missing approval gate for gated actions
- no secret leakage
- no cross-tenant or cross-user data leakage where isolation applies
- no direct obedience to untrusted injected instructions

## Evaluation Artifacts
Teams `SHOULD` maintain:
- a scenario matrix
- a safety invariant list
- baseline test cases
- validation rubrics
- ownership for evaluation maintenance

## Evaluation Frequency
At minimum:
- smoke tests `SHOULD` run on every meaningful change
- full evaluation suites `SHOULD` run before release
- regression baselines `SHOULD` run whenever prompts, tools, memory, or routing
  logic change

## Failure Interpretation
When an evaluation fails, the team `SHOULD` determine:
1. Is this a safety failure, contract failure, or quality failure?
2. Is the failure new or pre-existing?
3. Is the behavior blocked, degraded, or silently wrong?
4. Does the failure require rollback, redesign, or test adjustment?

## Anti-Patterns
- Evaluating only for eloquence or vibe
- Using one benchmark score as proof of production readiness
- Shipping with no red-team coverage
- Treating prompt changes as too small to require regression testing
- Ignoring partial failures because the final answer sounds plausible

## Validation
This book is complete when a team can derive:
1. what to test
2. how to test it
3. which failures block release
4. how to detect regression over time

## Adoption Notes
Teams do not need a perfect evaluation platform on day one, but they do need a
repeatable evaluation habit. The framework favors layered practical testing over
single-number confidence.
