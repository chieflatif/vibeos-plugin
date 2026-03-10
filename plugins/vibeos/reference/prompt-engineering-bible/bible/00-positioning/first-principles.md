# Book 2: First Principles

## Purpose
This book defines the universal philosophy of the framework.

## Applies To
This book applies to all agent types, all supported architectures, all prompt
contracts, all profiles, and all examples.

## Why It Matters
Without shared first principles, teams build agents that sound polished but act
unreliably. The purpose of these principles is to make agent behavior legible,
bounded, and trustworthy.

## Principle 1: Agents Are Operational Systems
- Agents `MUST` be designed as operating systems for decisions and actions, not
  as improvisational personalities.
- Prompts, tool policies, memory rules, and evaluation suites `MUST` be treated
  as system components.
- Any change that affects behavior `SHOULD` be governed as a product change.

## Principle 2: Trust Is the Product
- An agent `MUST NOT` trade truth for fluency.
- An agent `MUST` report uncertainty, missing data, and failed actions honestly.
- An agent `MUST` preserve the user's ability to understand what happened and
  what will happen next.

## Principle 3: Tools Beat Guessing
- If a system can verify through tools, it `MUST NOT` guess instead.
- An agent `MUST NOT` invent records, IDs, outputs, permissions, approvals, or
  execution results.
- A tool-using system `MUST` distinguish between verified data and inferred
  conclusions.

## Principle 4: Bounded Autonomy Beats Vague Helpfulness
- Agents `MUST` operate within explicit authority boundaries.
- Agents `MUST` know when to ask, when to act, and when to block.
- Autonomy `MUST` increase only when permissions, safeguards, and validation
  increase with it.

## Principle 5: Clarity Beats Theater
- Interaction quality `SHOULD` come from clarity, relevance, and good judgment,
  not from performative personality.
- Voice `MAY` improve trust and usability, but voice `MUST NOT` override safety,
  truth, or permission boundaries.
- A strong style is acceptable. A deceptive style is not.

## Principle 6: Context Is a Controlled Resource
- Context `MUST` be intentionally assembled, not accumulated indiscriminately.
- Systems `MUST` distinguish among working context, memory, and archival data.
- Teams `SHOULD` prefer targeted retrieval over loading everything available.

## Principle 7: Structure Enables Reliability
- Agent behavior `SHOULD` be expressed through explicit contracts whenever
  possible.
- Input assumptions, output obligations, safety boundaries, and failure modes
  `SHOULD` be written down.
- Teams `SHOULD` design prompts and agent contracts to be reviewable and
  testable.

## Principle 8: Evaluation Is Part of the System
- Agents `MUST NOT` be considered production-ready without evaluation.
- Scenario tests, safety tests, and regression checks `SHOULD` exist for any
  consequential agent behavior.
- Hard safety invariants `MUST` block release if violated.

## Principle 9: Architecture Is a Choice, Not a Religion
- The framework `MUST` support multiple architectures.
- Multi-agent orchestration `MAY` be appropriate for complex systems, but it
  `MUST NOT` be treated as mandatory.
- Simpler architectures `SHOULD` be preferred when they satisfy the product's
  requirements.

## Principle 10: Profiles Extend the Core
- Domain-specific methods `MUST` live in profiles unless they are broadly
  universal.
- A profile `MAY` add defaults, frameworks, tone guidance, or evaluation
  criteria for a domain.
- A profile `MUST NOT` silently redefine the universal core.

## System-Wide Commitments
All compliant implementations of this framework `MUST` be able to answer:
- What authority does this agent have?
- What may it do without approval?
- What evidence supports its claims?
- What happens when a tool fails?
- What information does it remember, and why?
- How is its behavior evaluated?

## Anti-Patterns
- Designing agents as personalities first and systems second
- Treating helpfulness as permission
- Hiding uncertainty behind polished language
- Using architecture complexity as a proxy for product quality
- Letting memory expand without policy
- Shipping untested prompt behavior into production

## Validation
This book is complete when later books can cite it without ambiguity and when
contributors can distinguish:
1. what is universally required
2. what depends on architecture
3. what belongs in a profile

## Adoption Notes
If a team adopts only one book from this framework, it should start here. These
principles are intended to remain stable even as specific templates, examples,
and profiles evolve.
