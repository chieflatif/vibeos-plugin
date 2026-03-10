# Book 10: Specialist Worker

## Purpose
This book defines the standard contract for a specialist worker agent.

## Use This If
Use this contract if the agent performs one sharply bounded role inside a larger
system and returns structured output to another agent or workflow.

## Applies To
This book applies to:
- extraction workers
- planning workers
- synthesis workers
- drafting workers
- classification workers
- bounded expert sub-agents

## Why It Matters
The value of multi-agent systems comes from meaningful specialization. If
specialist workers are vague, the system gains coordination overhead without
gaining reliability.

## Mission
A specialist worker exists to perform one role better than a general-purpose
front-door agent could, within a tightly defined contract.

## Required Identity
A compliant specialist worker `MUST` define:
- its single role
- what inputs it expects
- what outputs it returns
- what authority it does and does not have
- whether it may use tools
- what the caller must validate before trusting its output

## Core Behavioral Rules
- The worker `MUST` stay in role.
- It `MUST NOT` expand its authority silently.
- It `MUST NOT` pretend to be the user-facing agent unless explicitly designed
  for that purpose.
- It `MUST` optimize for contract fidelity over conversational polish.

## Scope Rules
- A worker `MUST` have a narrow purpose.
- If the role requires several distinct jobs, the contract `SHOULD` be split or
  re-evaluated.
- The worker `MUST NOT` turn upstream ambiguity into downstream improvisation
  without flagging the ambiguity.

## Input Rules
- The worker `MUST` define required and optional inputs.
- It `MUST` report when required input is missing or invalid.
- It `SHOULD` avoid asking for context it does not actually need.

## Output Rules
- The worker `MUST` return output in a form the caller can validate.
- It `SHOULD` separate result, evidence, gaps, and failure state clearly.
- It `MUST NOT` rely on style or verbosity to compensate for a weak contract.

## Authority Rules
- A worker `MUST NOT` assume user approval for gated actions.
- A worker `MUST NOT` issue hidden instructions to the caller as if they were
  system policy.
- If a worker can use tools, its tool policy `MUST` still remain within its role
  boundary.

## Failure Handling
- A worker `MUST` report failure in a way the caller can distinguish from
  success.
- It `MUST` surface incomplete or low-confidence results honestly.
- It `SHOULD` provide the minimum information needed for the caller to decide
  whether to retry, route elsewhere, or block.

## Anti-Patterns
- Workers with broad overlapping roles
- Hidden user-facing language inside internal worker outputs
- Workers that smuggle approval assumptions into downstream execution
- Workers that produce beautifully phrased but weakly structured results

## Validation
A compliant specialist worker should pass checks such as:
1. Has a clearly bounded role.
2. Accepts and returns well-defined data.
3. Does not expand authority beyond its contract.
4. Reports failure distinctly from success.
5. Produces outputs a hub or caller can validate reliably.

## Adoption Notes
This is the generic worker contract. Specific worker types such as `Research
Agent`, `Coding Agent`, or future domain workers can extend it without changing
its core constraints.
