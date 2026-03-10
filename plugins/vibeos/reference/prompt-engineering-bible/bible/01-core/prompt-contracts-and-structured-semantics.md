# Book 6: Prompt Contracts and Structured Semantics

## Purpose
This book defines the canonical contract model for prompts and agent
instructions.

## Applies To
This book applies to:
- system prompts
- agent contracts
- role prompts
- workflow prompts
- sub-agent instructions
- any prompt-derived artifact that governs behavior

## Why It Matters
Prompt quality becomes hard to validate when prompts are treated as prose. This
book makes prompts inspectable by defining the semantics they must carry,
regardless of whether they are written in XML, Markdown, YAML, JSON, or code.

## Core Rule
The framework's canonical requirement is not a specific markup language. The
canonical requirement is a complete structured contract with defined semantics.

- A compliant prompt artifact `MUST` contain the required semantic sections.
- XML `MAY` be used as a reference format.
- Other structured formats `MAY` be used if they preserve the same contract,
  constraints, and validation behavior.
- A prompt `MUST NOT` be considered compliant merely because it is in XML.

## Required Semantic Sections
Every consequential system prompt or agent prompt `MUST` define the following
sections, either explicitly or through an equivalent structured representation.

### 1. Identity
The prompt `MUST` define:
- role
- mission
- operating position
- authority scope
- intended user or upstream caller

### 2. Scope and Boundaries
The prompt `MUST` define:
- what the agent is responsible for
- what it must refuse or defer
- what it must never claim or expose

### 3. Inputs and Assumptions
The prompt `MUST` define:
- expected input types or upstream context
- how ambiguity is handled
- what the agent should do when required input is missing

### 4. Decision Policy
The prompt `MUST` define:
- when to act
- when to ask
- when to block
- when to escalate

### 5. Tool Policy
If the agent can use tools, the prompt `MUST` define:
- available tool classes or action classes
- confirmation requirements
- treatment of tool output as data rather than instructions
- failure handling for tool errors and timeouts

### 6. Output Contract
The prompt `MUST` define:
- required output shape
- required content elements
- forbidden content elements
- any formatting or brevity rules that matter operationally

### 7. Truth and Evidence Policy
The prompt `MUST` define:
- how verified facts differ from inference
- how uncertainty is expressed
- what happens when information is missing

### 8. Safety Policy
The prompt `MUST` define:
- treatment of untrusted input
- secret and sensitive-data handling
- restricted disclosures
- prompt-injection resistance expectations

### 9. Failure Contract
The prompt `MUST` define:
- how the agent responds to tool failures
- how the agent responds to incomplete results
- how the agent responds to policy conflicts
- how the agent reports blocked execution

## Recommended Semantic Sections
The following sections are not universally mandatory, but they `SHOULD` be
included for most production systems:
- context and memory policy
- evaluation hooks
- examples of correct and incorrect behavior
- voice and interaction rules
- architecture role in a larger system

## Format Guidance
### XML
XML `MAY` be used when:
- teams want explicit tags and strong structure
- prompts are validated against schemas
- the prompt artifact is intended to be machine-inspected directly

### Markdown or Structured Markdown
Markdown `MAY` be used when:
- prompts are maintained primarily by humans
- teams want readability during review
- semantic sections are still clearly delineated

### YAML or JSON
YAML or JSON `MAY` be used when:
- prompts are generated or transformed programmatically
- the prompt contract is consumed by tooling pipelines

### Code-Generated Prompts
Code-generated prompts `MAY` be used when:
- dynamic sections are assembled at runtime
- the generated prompt remains traceable to canonical source assets
- the semantic contract is still testable

## Reference Skeleton
The following is a reference semantic skeleton, not the only valid syntax.

```text
IDENTITY
SCOPE_AND_BOUNDARIES
INPUTS_AND_ASSUMPTIONS
DECISION_POLICY
TOOL_POLICY
OUTPUT_CONTRACT
TRUTH_AND_EVIDENCE
SAFETY_POLICY
FAILURE_CONTRACT
```

## Compliance Rules
- A prompt artifact `MUST` have a canonical source location.
- A prompt artifact `MUST` have version metadata.
- A prompt artifact `SHOULD` have an owner.
- A prompt artifact `SHOULD` declare dependent systems or agent types.
- A prompt artifact `MUST` be testable against at least one evaluation suite if
  it governs consequential behavior.
- Generated runtime prompts `MUST` be traceable to canonical source prompts.

## What Does Not Count as a Contract
The following are insufficient on their own:
- a persona paragraph
- a style guide with no decision rules
- a list of tool names without usage policy
- vague statements like "be helpful and safe"
- examples without explicit boundaries

## Anti-Patterns
- Treating XML as sufficient proof of quality
- Mixing mandatory rules and optional style preferences with no distinction
- Embedding domain assumptions in the base contract without labeling them
- Failing to specify blocked or failed states
- Allowing code-generated prompts with no canonical source of truth

## Validation
A prompt contract is valid when a reviewer can answer:
1. Who is this agent?
2. What is it allowed to do?
3. When does it ask versus act?
4. How does it use tools?
5. What must its output contain?
6. How does it handle uncertainty and failure?
7. Can this prompt be traced to a canonical source?

## Adoption Notes
Teams that already use XML do not need to abandon it. Teams that prefer code or
Markdown do not need to adopt XML. The framework standardizes semantics first,
then allows multiple concrete representations.
